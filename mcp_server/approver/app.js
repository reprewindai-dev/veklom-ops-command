/*
 * Veklom Gate Approver.
 *
 * Turns this browser into an approval device. The Ed25519 signing key is generated here as a
 * non-extractable WebCrypto key and stored in IndexedDB; it cannot be read out, only used to sign.
 * An approval link carries the exact call in the URL fragment (never sent to any server). This page
 * re-computes the parameter fingerprint, shows exactly what will run, and on a deliberate hold signs
 * one single-use approval bound to deployment + tool + action + exact parameters, then delivers it to
 * the deployment's endpoint that THIS DEVICE pinned when the deployment was trusted.
 *
 * Host this page on its own origin, never on the MCP server.
 */
"use strict";

(() => {
  const enc = new TextEncoder();
  const dec = new TextDecoder();
  const view = document.getElementById("view");
  const deviceChip = document.getElementById("device-chip");
  const deviceName = document.getElementById("device-name");
  const settingsDialog = document.getElementById("settings");
  const settingsBody = document.getElementById("settings-body");
  const HOLD_MS = 1100;
  const TTL_CHOICES = [120, 300, 600];

  // ---------- small utilities ----------

  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      if (key === "class") el.className = value;
      else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
      else if (value === true) el.setAttribute(key, "");
      else el.setAttribute(key, String(value));
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      el.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return el;
  }

  const store = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem("veklom-gate." + key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem("veklom-gate." + key, JSON.stringify(value)); } catch { /* storage unavailable */ }
    },
  };

  function b64url(bytes) {
    let bin = "";
    for (const b of bytes) bin += String.fromCharCode(b);
    return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  function b64urlToText(value) {
    const b64 = value.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((value.length + 3) % 4);
    const bin = atob(b64);
    return dec.decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  }

  function hex(buffer) {
    return Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, "0")).join("");
  }

  // Must match Python json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False).
  function canonical(value) {
    if (value === null) return "null";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "number") {
      if (!Number.isSafeInteger(value)) throw new Error("Only integer numbers can be fingerprinted identically.");
      return String(value);
    }
    if (typeof value === "string") return JSON.stringify(value);
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (typeof value === "object") {
      const keys = Object.keys(value).sort((a, b) => {
        const x = Array.from(a), y = Array.from(b);
        for (let i = 0; i < Math.min(x.length, y.length); i++) {
          const d = x[i].codePointAt(0) - y[i].codePointAt(0);
          if (d) return d;
        }
        return x.length - y.length;
      });
      return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonical(value[k])).join(",") + "}";
    }
    throw new Error("Unsupported value in parameters.");
  }

  async function sha256hex(text) {
    return hex(await crypto.subtle.digest("SHA-256", enc.encode(text)));
  }

  function fmtClock(seconds) {
    const s = Math.max(0, Math.floor(seconds));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }

  function fmtAgo(ms) {
    const s = Math.round((Date.now() - ms) / 1000);
    if (s < 60) return "just now";
    if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)} h ago`;
    return new Date(ms).toLocaleDateString();
  }

  function short(hexValue) {
    return hexValue.slice(0, 8) + "…" + hexValue.slice(-6);
  }

  // ---------- key storage (IndexedDB holds the non-extractable CryptoKey) ----------

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open("veklom-gate-approver", 1);
      req.onupgradeneeded = () => req.result.createObjectStore("keys");
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function idb(mode, fn) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction("keys", mode);
      const req = fn(tx.objectStore("keys"));
      tx.oncomplete = () => resolve(req && req.result);
      tx.onerror = () => reject(tx.error);
    });
  }

  const keys = {
    load: () => idb("readonly", (s) => s.get("signing-key")).catch(() => null),
    save: (record) => idb("readwrite", (s) => s.put(record, "signing-key")),
    remove: () => idb("readwrite", (s) => s.delete("signing-key")),
  };

  async function ed25519Supported() {
    try {
      await crypto.subtle.generateKey({ name: "Ed25519" }, false, ["sign", "verify"]);
      return true;
    } catch { return false; }
  }

  async function createKey() {
    const pair = await crypto.subtle.generateKey({ name: "Ed25519" }, false, ["sign", "verify"]);
    const raw = new Uint8Array(await crypto.subtle.exportKey("raw", pair.publicKey));
    const record = {
      privateKey: pair.privateKey,
      publicKey: pair.publicKey,
      publicB64: b64url(raw),
      fingerprint: (await sha256hex(b64url(raw))).slice(0, 16),
      createdAt: Date.now(),
    };
    await keys.save(record);
    const check = await keys.load();
    if (!check) throw new Error("This browser would not keep the key (private window or blocked storage).");
    return record;
  }

  // ---------- state ----------

  const state = {
    key: null,
    approver: store.get("approver", ""),
    deployments: store.get("deployments", {}), // aud -> { base: "https://ops.example.com", addedAt }
    history: store.get("history", []),
  };

  function saveDeployments() { store.set("deployments", state.deployments); }

  function remember(entry) {
    state.history = [{ ...entry, at: Date.now() }, ...state.history].slice(0, 25);
    store.set("history", state.history);
  }

  // ---------- request parsing ----------

  function parseRequest() {
    const match = location.hash.match(/^#r=([A-Za-z0-9_-]+)$/);
    if (!match) return null;
    let req;
    try { req = JSON.parse(b64urlToText(match[1])); } catch { return { error: "This approval link is damaged. Ask the agent for a fresh link." }; }
    const ok = req && typeof req === "object"
      && ["aud", "tool", "action"].every((k) => typeof req[k] === "string" && req[k].length > 0 && req[k].length < 200)
      && req.params && typeof req.params === "object" && !Array.isArray(req.params)
      && typeof req.params_sha256 === "string" && /^[0-9a-f]{64}$/.test(req.params_sha256)
      && Number.isSafeInteger(req.expires_after_seconds) && req.expires_after_seconds > 0;
    if (!ok) return { error: "This approval link is missing required fields. Ask the agent for a fresh link." };
    return { req };
  }

  const VERBS = {
    stop_container: ["Stop", "container"],
    start_stopped_container: ["Start", "container"],
    restart_container: ["Restart", "container"],
  };

  function describe(req) {
    const [verb, noun] = VERBS[req.tool] || [req.tool.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()), ""];
    const target = req.params.container ?? Object.values(req.params).find((v) => typeof v === "string") ?? "";
    return { verb, noun, target: String(target) };
  }

  function deliverUrl(base) {
    return base.replace(/\/+$/, "") + "/approvals/deliver";
  }

  function baseFromDeliver(url) {
    try {
      const u = new URL(url);
      if (!/^https?:$/.test(u.protocol)) return null;
      return u.origin + u.pathname.replace(/\/approvals\/deliver\/?$/, "");
    } catch { return null; }
  }

  // ---------- views ----------

  function render(...nodes) {
    view.replaceChildren(...nodes);
    document.getElementById("main").focus({ preventScroll: true });
  }

  function updateChip() {
    deviceChip.hidden = !state.key;
    deviceName.textContent = state.approver || "This device";
  }

  function viewUnsupported() {
    render(h("section", { class: "card" },
      h("div", { class: "pad stack" },
        h("p", { class: "eyebrow" }, "Not available in this browser"),
        h("h1", {}, "This browser can't hold a signing key"),
        h("p", { class: "lede" }, "The approver needs Ed25519 in WebCrypto. Use a current Chrome, Edge, Safari or Firefox, over HTTPS (or localhost)."),
      )));
  }

  function viewSetup(pendingRequest) {
    const nameInput = h("input", { id: "approver-name", autocomplete: "name", required: true, maxlength: 80, placeholder: "e.g. founder:alex", value: state.approver });
    const status = h("p", { class: "muted", role: "status" });
    const create = h("button", {
      class: "btn primary", type: "button",
      onclick: async () => {
        const name = nameInput.value.trim();
        if (!name) { status.textContent = "Add a name first. It is written into every approval you sign."; nameInput.focus(); return; }
        create.disabled = true;
        status.textContent = "Creating a key that never leaves this device…";
        try {
          state.approver = name;
          store.set("approver", name);
          state.key = await createKey();
          updateChip();
          viewKeyCreated(pendingRequest);
        } catch (err) {
          create.disabled = false;
          status.textContent = err.message || "Could not create a key.";
        }
      },
    }, "Create signing key");

    render(h("section", { class: "card" },
      h("div", { class: "pad stack" },
        h("p", { class: "eyebrow" }, "Set up"),
        h("h1", {}, "Make this device an approver"),
        h("p", { class: "lede" }, "Your agent can ask for risky actions. This device decides. It creates a signing key that can't be copied out of this browser; the server only ever gets the public half."),
        h("div", { class: "field" },
          h("label", { for: "approver-name" }, "Your approver name"),
          nameInput,
          h("span", { class: "help" }, "Recorded with each approval in the audit log."),
        ),
        create,
        status,
      )));
  }

  function copyButton(text, label) {
    const btn = h("button", {
      class: "btn small", type: "button",
      onclick: async () => {
        try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
        catch { btn.textContent = "Select and copy manually"; }
        setTimeout(() => { btn.textContent = label; }, 1800);
      },
    }, label);
    return btn;
  }

  function publicKeyBox() {
    const line = `VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64=${state.key.publicB64}`;
    return h("div", { class: "keybox" },
      h("p", { class: "label" }, "Public key for your server"),
      h("code", {}, state.key.publicB64),
      h("div", { class: "envline" }, line),
      h("div", { class: "row" }, copyButton(line, "Copy env line"), h("span", { class: "muted" }, `Fingerprint ${state.key.fingerprint}`)),
    );
  }

  function viewKeyCreated(pendingRequest) {
    render(h("section", { class: "card" },
      h("div", { class: "pad stack" },
        h("p", { class: "eyebrow" }, "Device ready"),
        h("h1", {}, "Give your server the public key"),
        h("p", { class: "lede" }, "Set this on the Veklom Gate MCP server and restart it. Only this device can now approve its high-risk actions."),
        publicKeyBox(),
        h("button", { class: "btn primary", type: "button", onclick: () => route(pendingRequest) }, pendingRequest ? "Continue to the request" : "Done"),
      )));
  }

  function viewIdle() {
    const deployments = Object.keys(state.deployments);
    render(
      h("section", { class: "card" },
        h("div", { class: "empty" },
          h("div", { class: "radar", "aria-hidden": "true" }, h("span"), h("span"), h("span"), h("i")),
          h("h1", {}, "Nothing to approve"),
          h("p", { class: "lede" }, "When your agent needs permission, it gives you a link. Open it on this device to see exactly what it wants to do."),
          deployments.length
            ? h("p", { class: "muted" }, `Trusted deployments: ${deployments.join(", ")}`)
            : h("p", { class: "muted" }, "No deployments trusted yet. The first approval link from a deployment will ask you to trust it."),
        )),
      state.history.length ? h("section", { class: "card gap-top" },
        h("div", { class: "pad" },
          h("p", { class: "label" }, "Recent on this device"),
          h("ul", { class: "history" }, state.history.map((item) =>
            h("li", {},
              h("span", { class: "what" }, `${item.verb} `, h("code", {}, item.target), ` · ${item.aud}`,
                h("span", { class: `tag ${item.outcome === "approved" ? "ok" : item.outcome === "declined" ? "no" : "bad"}` }, item.outcome)),
              h("span", { class: "when" }, fmtAgo(item.at)),
            ))),
        )) : null,
    );
  }

  function viewError(message) {
    render(h("section", { class: "card" },
      h("div", { class: "pad stack" },
        h("div", { class: "notice bad" }, h("span", { "aria-hidden": "true" }, "!"), h("div", {}, h("b", {}, "Nothing was signed"), message)),
        h("button", { class: "btn", type: "button", onclick: () => { history.replaceState(null, "", location.pathname); route(null); } }, "Close"),
      )));
  }

  function viewTrust(req) {
    const suggested = req.deliver_to ? baseFromDeliver(req.deliver_to) : null;
    const urlInput = h("input", { id: "deploy-url", inputmode: "url", value: suggested || "", placeholder: "https://ops.example.com", required: true });
    const status = h("p", { class: "muted", role: "status" });
    render(h("section", { class: "card" },
      h("div", { class: "ribbon medium" }, h("span", {}, "New deployment"), null),
      h("div", { class: "pad stack" },
        h("p", { class: "eyebrow" }, "Trust check"),
        h("h1", {}, "Trust this deployment?", h("span", { class: "target" }, req.aud)),
        h("p", { class: "lede" }, "This device hasn't approved anything for this deployment yet. Confirm where its Veklom Gate server lives. Approvals for it will only ever be delivered there."),
        h("div", { class: "field" },
          h("label", { for: "deploy-url" }, "Server address"),
          urlInput,
          h("span", { class: "help" }, suggested ? "Suggested by the link. Check it is your server before trusting it." : "The public address of the MCP server for this deployment."),
        ),
        h("div", { class: "row" },
          h("button", {
            class: "btn primary", type: "button",
            onclick: () => {
              let base;
              try {
                const u = new URL(urlInput.value.trim());
                if (!/^https?:$/.test(u.protocol)) throw new Error();
                if (u.protocol === "http:" && !/^(localhost|127\.0\.0\.1)$/.test(u.hostname)) throw new Error("https");
                base = (u.origin + u.pathname).replace(/\/+$/, "");
              } catch (err) {
                status.textContent = err.message === "https" ? "Use https:// (plain http is only allowed for localhost)." : "Enter a full address starting with https://";
                return;
              }
              state.deployments[req.aud] = { base, addedAt: Date.now() };
              saveDeployments();
              viewRequest(req);
            },
          }, "Trust this deployment"),
          h("button", { class: "btn ghost", type: "button", onclick: () => decline(req) }, "Not mine"),
        ),
        status,
      )));
  }

  async function viewRequest(req) {
    const deployment = state.deployments[req.aud];
    if (!deployment) return viewTrust(req);

    let computed;
    try { computed = await sha256hex(canonical(req.params)); }
    catch (err) { return viewError(err.message); }
    const fingerprintOk = computed === req.params_sha256;
    const linkBase = req.deliver_to ? baseFromDeliver(req.deliver_to) : null;
    const linkMismatch = linkBase && linkBase !== deployment.base;
    const { verb, noun, target } = describe(req);
    const tier = ["high", "medium", "low"].includes(req.risk_tier) ? req.risk_tier : "high";
    const maxTtl = Math.min(req.expires_after_seconds, 3600);
    const ttls = TTL_CHOICES.filter((t) => t <= maxTtl);
    if (!ttls.length) ttls.push(maxTtl);
    let ttl = ttls.includes(300) ? 300 : ttls[ttls.length - 1];

    const checks = h("ul", { class: "checks" },
      h("li", { class: fingerprintOk ? "ok" : "bad" },
        h("span", { class: "ic", "aria-hidden": "true" }, fingerprintOk ? "✓" : "✕"),
        h("div", {}, fingerprintOk ? "Parameters match their fingerprint" : "Parameters do not match their fingerprint — refusing to sign",
          h("small", {}, short(computed)))),
      h("li", { class: "ok" },
        h("span", { class: "ic", "aria-hidden": "true" }, "✓"),
        h("div", {}, "Deployment is trusted on this device", h("small", {}, deployment.base))),
      linkMismatch ? h("li", { class: "warn" },
        h("span", { class: "ic", "aria-hidden": "true" }, "!"),
        h("div", {}, "The link suggested a different server. It will be ignored.", h("small", {}, linkBase))) : null,
      h("li", { class: "ok" },
        h("span", { class: "ic", "aria-hidden": "true" }, "✓"),
        h("div", {}, "Works once, for exactly this call, on this deployment")),
    );

    const ttlGroup = h("div", { class: "ttl", role: "radiogroup", "aria-label": "Approval valid for" },
      ttls.map((t) => h("label", {},
        h("input", { type: "radio", name: "ttl", value: t, checked: t === ttl, onchange: () => { ttl = t; } }),
        h("span", {}, t < 120 ? `${t} s` : `${Math.round(t / 60)} min`),
      )));

    const hold = h("button", {
      class: `hold${tier === "high" ? " high-risk" : ""}`, type: "button", disabled: !fingerprintOk,
      "aria-describedby": "hold-help",
    }, h("span", {}, "Hold to approve once"), h("span", { class: "hint", "aria-hidden": "true" }, "· press and hold"));
    attachHold(hold, () => approve(req, deployment, ttl, hold));

    render(h("section", { class: "card" },
      h("div", { class: `ribbon ${tier}` }, h("span", {}, `${tier} risk`), h("span", { class: "timer" }, req.request_id ? `#${String(req.request_id).slice(0, 8)}` : "")),
      h("div", { class: "pad" },
        h("p", { class: "eyebrow" }, "Your agent is asking to"),
        h("h1", {}, `${verb} ${noun}`.trim(), h("span", { class: "target" }, target || "(see parameters)")),
        h("div", { class: "where" }, "on ", h("code", {}, req.aud)),
        req.reason ? h("p", { class: "lede" }, req.reason) : null,
      ),
      h("div", { class: "pad section" },
        h("p", { class: "label" }, "Exact call"),
        h("dl", { class: "kv" }, h("dt", {}, "tool"), h("dd", {}, req.tool), h("dt", {}, "action"), h("dd", {}, req.action)),
        h("pre", { class: "json" }, JSON.stringify(req.params, null, 2)),
      ),
      h("div", { class: "pad section" }, h("p", { class: "label" }, "Checks"), checks),
      h("div", { class: "pad section stack" },
        h("p", { class: "label" }, "Approval valid for"),
        ttlGroup,
        h("div", { class: "actions" },
          hold,
          h("p", { class: "muted", id: "hold-help" }, `Signs as ${state.approver}. Keyboard: hold Space or Enter.`),
          h("button", { class: "btn ghost", type: "button", onclick: () => decline(req) }, "Decline"),
        ),
      ),
    ));
  }

  function attachHold(button, onComplete) {
    let start = 0, frame = 0, done = false;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / HOLD_MS);
      button.style.setProperty("--p", p.toFixed(3));
      if (p >= 1) { done = true; button.classList.remove("active"); button.classList.add("done"); onComplete(); return; }
      frame = requestAnimationFrame(tick);
    };
    const begin = (event) => {
      if (button.disabled || done || start) return;
      if (event.type === "keydown") { if (event.repeat || (event.key !== " " && event.key !== "Enter")) return; event.preventDefault(); }
      if (event.type === "pointerdown") { try { button.setPointerCapture(event.pointerId); } catch { /* not capturable; hold still works */ } }
      start = performance.now();
      button.classList.add("active");
      frame = requestAnimationFrame(tick);
    };
    const cancel = (event) => {
      if (done || !start) return;
      if (event && event.type === "keyup" && event.key !== " " && event.key !== "Enter") return;
      cancelAnimationFrame(frame);
      start = 0;
      button.classList.remove("active");
      button.style.setProperty("--p", "0");
    };
    button.addEventListener("pointerdown", begin);
    button.addEventListener("keydown", begin);
    ["pointerup", "pointercancel", "pointerleave", "keyup", "blur"].forEach((t) => button.addEventListener(t, cancel));
    button.addEventListener("click", (e) => e.preventDefault());
    button.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  async function sign(req, ttl) {
    const now = Math.floor(Date.now() / 1000);
    const claims = {
      v: 2,
      nonce: b64url(crypto.getRandomValues(new Uint8Array(18))),
      aud: req.aud,
      tool: req.tool,
      action: req.action,
      params_sha256: req.params_sha256,
      approved_by: state.approver,
      issued_at: now,
      expires_at: now + ttl,
    };
    const payload = enc.encode(JSON.stringify(claims));
    const signature = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, state.key.privateKey, payload));
    return { token: `v2.${b64url(payload)}.${b64url(signature)}`, claims };
  }

  async function approve(req, deployment, ttl, button) {
    button.disabled = true;
    button.firstChild.textContent = "Signing…";
    let signed;
    try { signed = await sign(req, ttl); }
    catch (err) { return viewError(`Signing failed: ${err.message}`); }
    const { verb, target } = describe(req);
    let delivered = false, failure = "";
    try {
      const res = await fetch(deliverUrl(deployment.base), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: signed.token }),
        credentials: "omit",
        referrerPolicy: "no-referrer",
      });
      const body = await res.json().catch(() => ({}));
      delivered = res.ok && body.delivered === true;
      if (!delivered) failure = body.error || `Server answered ${res.status}.`;
    } catch {
      failure = "Couldn't reach the server from this device.";
    }
    remember({ aud: req.aud, verb, target, outcome: delivered ? "approved" : "not delivered" });
    history.replaceState(null, "", location.pathname);
    viewApproved(req, signed, delivered, failure);
  }

  function viewApproved(req, signed, delivered, failure) {
    const { verb, noun, target } = describe(req);
    const timer = h("div", { class: "big-timer", role: "timer", "aria-live": "off" }, fmtClock(signed.claims.expires_at - Date.now() / 1000));
    const interval = setInterval(() => {
      const left = signed.claims.expires_at - Date.now() / 1000;
      timer.textContent = fmtClock(left);
      if (left <= 0) { clearInterval(interval); timer.textContent = "expired"; }
    }, 500);
    const tick = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7"/></svg>';
    const cross = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg>';
    const seal = h("div", { class: `seal${delivered ? "" : " failed"}` });
    seal.innerHTML = delivered ? tick : cross; // static markup only
    render(h("section", { class: "card" },
      h("div", { class: "success" },
        seal,
        h("h1", {}, delivered ? "Approved once" : "Signed, not delivered"),
        h("p", { class: "lede" }, delivered
          ? `${verb} ${noun} ${target} on ${req.aud} can now run one time. Your agent picks it up automatically.`
          : `${failure} You can give the agent this approval directly instead.`),
        timer,
        h("p", { class: "muted" }, "until this approval expires unused"),
      ),
      delivered ? null : h("div", { class: "pad section stack" },
        h("p", { class: "label" }, "Approval token"),
        h("pre", { class: "json" }, signed.token),
        copyButton(signed.token, "Copy token"),
      ),
      h("div", { class: "pad section row spread" },
        h("span", { class: "muted" }, `Signed as ${state.approver}`),
        h("button", { class: "btn small", type: "button", onclick: () => { clearInterval(interval); route(null); } }, "Done"),
      ),
    ));
  }

  function decline(req) {
    const { verb, target } = describe(req);
    remember({ aud: req.aud, verb, target, outcome: "declined" });
    history.replaceState(null, "", location.pathname);
    const seal = h("div", { class: "seal declined" });
    seal.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"/></svg>';
    render(h("section", { class: "card" },
      h("div", { class: "success" },
        seal,
        h("h1", {}, "Declined"),
        h("p", { class: "lede" }, "Nothing was signed or sent. The agent's request will simply expire."),
        h("button", { class: "btn", type: "button", onclick: () => route(null) }, "Done"),
      )));
  }

  // ---------- settings ----------

  function openSettings() {
    const list = h("ul", { class: "deployments" },
      Object.entries(state.deployments).map(([aud, d]) =>
        h("li", {},
          h("div", { class: "meta" }, h("code", {}, aud), h("small", {}, d.base)),
          h("button", { class: "btn small danger", type: "button", onclick: () => { delete state.deployments[aud]; saveDeployments(); openSettings(); } }, "Remove"),
        )));
    settingsBody.replaceChildren(
      h("div", { class: "stack" },
        h("p", { class: "muted" }, `Signing as ${state.approver} · key created ${fmtAgo(state.key.createdAt)}`),
        publicKeyBox(),
        h("div", {},
          h("p", { class: "label" }, "Trusted deployments"),
          Object.keys(state.deployments).length ? list : h("p", { class: "muted" }, "None yet."),
        ),
        h("div", { class: "notice" }, h("span", { "aria-hidden": "true" }, "!"),
          h("div", {}, h("b", {}, "Replace this device's key"),
            "Use this if the device is lost or shared. Approvals from the old key stop working once your server has the new public key.")),
        h("button", {
          class: "btn danger", type: "button",
          onclick: async () => {
            if (!confirm("Delete this device's signing key? It cannot be recovered.")) return;
            await keys.remove();
            state.key = null;
            settingsDialog.close();
            updateChip();
            route(parseRequest());
          },
        }, "Delete signing key"),
      ));
    if (!settingsDialog.open) settingsDialog.showModal();
  }

  deviceChip.addEventListener("click", openSettings);

  // ---------- routing ----------

  function route(parsed) {
    if (parsed && parsed.error) return viewError(parsed.error);
    const req = parsed && parsed.req;
    if (!state.key) return viewSetup(parsed);
    if (req) return viewRequest(req);
    return viewIdle();
  }

  window.addEventListener("hashchange", () => route(parseRequest()));

  (async () => {
    if (!window.isSecureContext || !crypto.subtle || !(await ed25519Supported())) return viewUnsupported();
    state.key = await keys.load();
    updateChip();
    route(parseRequest());
  })();
})();
