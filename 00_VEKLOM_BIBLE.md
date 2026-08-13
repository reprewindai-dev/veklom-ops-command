# 00 — VEKLOM CANONICAL BIBLE

> **READ THIS FIRST.** This is the canonical architecture + runtime-truth contract for Veklom.
> It supersedes older “Golden Bible”, agent-alignment, deployment-topology, port-doctrine, and infrastructure-constant documents wherever they conflict.
>
> **Last runtime verification:** 2026-08-09 01:42 UTC, using owner-supplied Coolify 4.1.2 screens, active Traefik dynamic configuration, proxy logs, Sentinel logs, and Coolify Advanced settings.
> **Last repository verification:** 2026-08-09 against GitHub default branches.
> **Rule:** a claim that has not been independently reverified must be labeled `LAST_KNOWN`, `CONFIGURED`, `UNVERIFIED`, or `TARGET` — never presented as production fact.

---

## 1. Truth Hierarchy

When sources disagree, use this order:

1. **Public behavior / live endpoint proof** — what the deployed domain actually returns now.
2. **Coolify runtime state** — active applications, containers, environment bindings, proxy configuration, server status.
3. **GitHub default branch** — source-code truth and change history.
4. **PGL / Gnomledger evidence** — execution evidence only when the record is actually persisted/sealed and verifiable.
5. **Documentation** — explanatory only. Documentation never overrides live state.

A merged PR is not deployment proof. A running container is not product proof. A screenshot is evidence of the screen at that time, not proof of every downstream claim.

### Completion standard

A production change is complete only after:

`repo change → pushed commit → deployed runtime → live endpoint/UI verification → evidence/report`

Synthetic data, seeded fixtures, local success, or pasted text must never be upgraded into “production verified” language.

---

## 2. Product Doctrine — Capability-Centric, Not Agent-Centric

**Veklom is the sovereign AI capability control plane / runtime authority layer.**

Veklom governs **capability**, not a permanent fleet of privileged agents. A human, model, service, script, or machine can request an outcome; none receives a governance bypass.

Canonical execution lifecycle:

`Resolve capability → Bind policy + authority → Issue scoped grant → Instantiate ephemeral worker/runtime → Execute → Record evidence → Revoke authority → Destroy worker/runtime → Observe / Settle when applicable`

The stable object is the **capability contract**, including inputs, outputs, preconditions, effects, authority requirements, resource/budget bounds, recovery/revocation behavior, evidence requirements, and version compatibility.

### Standalone products vs Capability OS

Some Veklom-built systems are independently sellable products. Their standalone UI is **not** embedded wholesale inside Capability OS.

- **Project Genome Ledger / PGL** can expose its own registry, certificates, lineage, ledger, exports, and billing as a standalone product. Inside Veklom, its provenance/evidence/lineage capabilities are rebuilt into Veklom-native surfaces.
- **ABIDE** can have its own standalone blueprint workbench. Inside Veklom, its blueprint/contract capabilities appear as native Capability OS functions.
- The same rule applies to RepoGate, Apex, Discovery, and other reusable Veklom modules: reuse the domain logic/capability; do not paste standalone product pages into the OS.

---

## 3. Canonical Component Responsibilities

| Domain | Canonical responsibility |
|---|---|
| **VCCP** | Capability control plane: outcome compilation, capability resolution/orchestration, authority lifecycle coordination. |
| **UCH / UCR** | Universal capability packaging + runtime resolution/execution model. |
| **cAPI / Covenant** | Governed connection layer: capability discovery/connection, request governance phases, evidence handoff. |
| **CAPPO** | Fail-closed runtime governance / LAW 0 authorization boundary for consequential execution. |
| **ABIDE** | Blueprint + bounded execution-contract compilation. |
| **Lockerphycer** | Secret/key security domain. Never claim HSM/TEE/hardware-enclave guarantees unless the deployed implementation proves them. |
| **BYOS** | Sovereign execution substrate/provider; not the only possible execution substrate. |
| **Gnomledger / PGL** | Evidence, provenance, lineage, append-only/hash-linked records, verification surfaces. “Tamper-evident” is the default claim unless stronger immutability is independently proven. |
| **VNP** | Measurement, telemetry, routing/observation evidence. |
| **RepoGate** | Repository/capability intake, inspection, findings, policy/security gating. |
| **Veklom ID** | Identity/trust events and identity-side verification. |
| **x402** | Settlement/payment integration where verified; payment is not automatically proof of execution. |

### No absolute marketing claims without proof

Do not claim “100% production ready”, certification/compliance, hardware enclave protection, “secrets never enter software memory”, “prompt injection eliminated”, physical immutability, sub-microsecond global quarantine, or on-chain finality merely because a README or diagram says so. Use exact, testable language backed by current evidence.

---

## 4. Current Working Repository Set

These repositories participate directly in the current Veklom capability/runtime stack and inherit this Bible:

- `reprewindai-dev/veklom-ops-command`
- `reprewindai-dev/veklom-byos-backend`
- `reprewindai-dev/cappo-backend`
- `reprewindai-dev/cAPI`
- `reprewindai-dev/gnomledger`
- `reprewindai-dev/lockerphycer`
- `reprewindai-dev/VCCP`
- `reprewindai-dev/ABIDE`
- `reprewindai-dev/veklom-FRONTEND`
- `reprewindai-dev/veklom-vnp`
- `reprewindai-dev/veklomdiscovery`
- `reprewindai-dev/Veklom-ID`
- `reprewindai-dev/real-repo-gate-for-veklom`
- `reprewindai-dev/apex`

Historical experiments, duplicate repos, generated prototypes, and old `uacp*` variants are not automatically canonical because they exist.

---

## 5. Operations Rules

### Cloudflare and Perimeter Security

- **Web Bot Auth:** Cloudflare provides the initial perimeter for bot verification via `/.well-known/http-message-signatures-directory` and Ed25519 signed requests.
- **Authority:** Web Bot Auth proves identity at the perimeter but does *not* grant verified capability execution. CAPPO retains exclusive authority over consequential execution, mount validity, and token generation.
- **cAPI Role:** cAPI verifies the Cloudflare `Signature` headers and proxies the verified identity to CAPPO. It does not synthesize grants. CAPPO and cAPI configurations must remain separate; never alias `CAPPO_BACKEND_URL` to `CAPI_RUNTIME_URL`.

### Coolify and GitHub

- **GitHub default branch = source truth.**
- **Coolify = deployment/runtime configuration truth.**
- Environment secrets belong in deployment secret management, not committed `.env` files.
- Emergency runtime fixes must be reconciled back into GitHub.
- Never publish credentials, tokens, private keys, or secret values in issues, docs, chat, screenshots, or logs.

### Coolify management method

- Use the **Coolify UI/API/MCP** for Coolify resource management where available.
- Coolify's MCP endpoint is exposed by the Coolify instance itself and authenticated with a bearer token created under Coolify Security/API Tokens.
- SSH is reserved for **direct host/container verification or operations** that cannot be performed safely through Coolify.
- Do not turn routine Coolify management into ad-hoc SSH editing.

### Docker networking

- `localhost` means the current container/process namespace.
- Inter-container traffic should use stable service/container DNS or an explicitly managed endpoint.
- Do not hard-code ephemeral Coolify-generated container IDs into product source when a stable service name/config variable exists.

### Host-port reservations vs internal container ports — VERIFIED / CORRECTED

This distinction is mandatory.

**Host ports are infrastructure-owned and may be reserved. Internal Docker ports are separate.**

Current verified host bindings/reservations on Server 0 include:

- **Host `80` / `443`** — Traefik public ingress.
- **Host `8000`** — **Coolify itself**. The Coolify UI is reached on `:8000`, and Coolify's MCP endpoint is `http://<coolify-host>:8000/mcp`. **Do not publish a Veklom application directly on host port 8000.**
- **Host `8080`** — bound by the Coolify Traefik proxy configuration for its internal API/dashboard service path. Do not allocate it to an unrelated host-published application without first changing and revalidating proxy ownership.

**Internal container port `8000` is not the same thing as host port `8000`.** A container may listen on internal `8000` when that port is only reachable on the Docker network and Traefik routes to it. The current Gnomledger `ledger.veklom.com` route is configured this way.

The same distinction applies to `3000`: multiple current services are configured to listen on internal Docker port `3000` behind Traefik. That does **not** prove host port `3000` is free. The prior reason for reserving host `3000` has not yet been reverified in the 2026-08-09 Coolify evidence, so **do not allocate host port 3000 until it is explicitly reverified**.

Canonical rule:

1. Never choose a host-published port from memory.
2. Check current Coolify/host bindings first.
3. Public services normally enter through Traefik `80/443` and route to an internal container port.
4. Internal `3000`/`8000` are allowed when isolated behind Docker/Traefik; host `8000` is currently reserved by Coolify.

---

## 6. Server 0 / Coolify Master — VERIFIED 2026-08-09

Private operational detail; do not copy this section into public documentation.

| Property | Verified value |
|---|---|
| Coolify | `v4.1.2` |
| Coolify server name | `localhost` |
| Host | `5.78.135.11` |
| OS | Ubuntu `22.04.5 LTS` |
| Architecture | `x86_64` |
| Kernel | `5.15.0-177-generic` |
| CPU | `3` cores |
| RAM | `3.7 GB` |
| Server timezone | `UTC` |
| Proxy | Running |
| Sentinel | In Sync |
| Coolify MCP | exposed at Coolify `:8000/mcp` when enabled; bearer-token authenticated |

### Sentinel — VERIFIED

Current configuration shown in Coolify:

- Coolify URL: `http://host.docker.internal:8000`
- metrics sampling: `10s`
- metrics history: `7 days`
- push interval: `60s`

Owner-supplied live Sentinel logs on 2026-08-09 show repeated `200` health responses, periodic pushes to `/api/v1/sentinel/push`, and successful CPU/memory history queries.

### CA certificate — VERIFIED SCREEN STATE

Coolify showed its CA certificate as valid until `2036-05-15 00:23:57` and the recommended mount path:

`/data/coolify/ssl/coolify-ca.crt:/etc/ssl/certs/coolify-ca.crt:ro`

Only mount it where a container actually needs to trust Coolify-managed database TLS.

---

## 7. Traefik Proxy — VERIFIED 2026-08-09

Owner-provided Coolify configuration shows:

- proxy container: `coolify-proxy`
- configured image branch: `traefik:v3.6`
- installed version reported by Coolify: `v3.6.25`
- bindings: `80:80`, `443:443`, `443:443/udp`, `8080:8080`
- Docker provider enabled
- file provider directory: `/traefik/dynamic/`
- file watch enabled
- `exposedByDefault=false`
- ACME HTTP challenge via the `http` entrypoint

Coolify reports a newer Traefik `v3.7` minor line is available. Do not perform a production minor upgrade solely because the notice appears. Back up proxy state, review upstream migration notes, test the exact dynamic configuration, then upgrade through the supported Coolify flow.

---

## 8. Active Traefik Dynamic Routes — CONFIGURED 2026-08-09

`CONFIGURED` means present in the active dynamic configuration screen. It does not by itself prove the upstream service is healthy.

| Host | Configured target |
|---|---|
| `apex.veklom.com` | `apex-blueprint-node:3011` |
| `bingo.veklom.com` | `bingo-backend:3000` |
| `capi.veklom.com` | current Coolify cAPI application target on `3003` |
| `cappo.veklom.com` | `cappo-backend-node:8002` |
| `discovery.veklom.com` | `veklomdiscovery:3000` |
| `duel.veklom.com` | `agent-duel-backend:3000` |
| `id.veklom.com` | `veklom-id:3000` |
| `interlink.veklom.com` | current Coolify Interlink application target on `3000` |
| `ledger.veklom.com` | `gnomledger-api-1:8000` |
| `lockerphycer.veklom.com` | `lockerphycer-api:8092` |
| `pgl.veklom.com` | `gnomledger-api-1:8001` |
| `repogate.veklom.com` | `veklom-repo-gate:3000` |
| `api.veklom.com` | current BYOS application target on `8088` |
| `control.veklom.com` / `app.veklom.com` | current control-plane target on `3002` in `veklom.yaml` |

Old `.bak` and `.disabled*` route files are historical artifacts and must not be treated as active topology.

---

## 9. KNOWN PRODUCTION ISSUE — ACME / ROOT DOMAIN ROUTING

Traefik logs supplied for the 2026-08-09 verification window show failed Let’s Encrypt HTTP-01 renewals for combinations of `veklom.com`, `www.veklom.com`, and `app.veklom.com`. The challenge requests resolve through Cloudflare addresses and return `404` from `/.well-known/acme-challenge/...`.

The dynamic configuration also contains overlapping root-domain intent (`veklom-redirect.yaml` and `veklom.yaml`). Determine which origin owns each hostname, make DNS/proxy/router ownership unambiguous, then retest certificate issuance. Do not describe root-domain renewal as healthy merely because an existing certificate still serves HTTPS.

---

## 10. Data / Persistence Doctrine

- Browser frontends do not connect directly to PostgreSQL.
- Frontends call authenticated service APIs.
- Database topology is runtime configuration, not a hard-coded product assumption.
- Prefer domain separation and least-privilege credentials over one unrestricted account.
- Never create a new hosted database merely because an old document says one exists or does not exist; verify current ownership and migration requirements first.

Older July documents containing exact PostgreSQL/Redis container IDs and a multi-database layout are `LAST_KNOWN` until each resource is revalidated in current Coolify state.

---

## 11. Evidence Standard

Distinguish:

- **assertion** — a claim in text
- **runtime observation** — logs/UI/API output
- **persisted evidence** — durable record tied to an execution
- **cryptographically verified evidence** — signatures/hash-chain/anchor verification actually checked
- **external finality** — independent anchor/settlement confirmed against its authoritative system

A hash chain is **tamper-evident**. Do not automatically call it physically immutable or undeletable.

Reason-rich evidence should prefer structured fields such as `policy_id`, `policy_version`, `rule_id`, `jurisdiction`, `classification`, `decision`, `reason_code`, `evaluator_version`, `input_hash`, `output_hash`, `authority_grant`, `delegation_chain`, `execution_id`, and verification state.

---

## 12. Documentation Governance

Every participating repository must place a conspicuous link to this Bible at the top of its README and maintain a root `00_VEKLOM_BIBLE.md` mirror/pointer.

When an older document overlaps with this Bible:

1. Preserve it under `docs/archive/<date>/` when it has historical value.
2. Replace the old root file with a short deprecation pointer when agents/tools may still discover that filename.
3. Never maintain two competing canonical topology documents.
4. Repo-specific docs may describe local APIs/build/test behavior, but must defer cross-repo architecture, deployment ownership, and runtime topology to this Bible.

Use status labels: `VERIFIED_LIVE`, `VERIFIED_REPO`, `CONFIGURED`, `LAST_KNOWN`, `TARGET`, `UNVERIFIED`, `DEMO`, `ARCHIVED`.

---

## 13. Update Protocol

Before changing this Bible:

1. Identify the exact claim being changed.
2. Verify source truth in the relevant GitHub default branch.
3. Verify runtime truth in Coolify / the deployed endpoint when the claim concerns production.
4. Record the verification date and evidence type.
5. Update dependent repo mirrors/pointers.
6. Archive superseded canonical docs.
7. If runtime and source disagree, record the drift explicitly instead of choosing the more convenient story.

**The Bible is not true because it is called the Bible. It is canonical because every factual claim is either verified, qualified, or explicitly marked unknown.**
