# 00 — VEKLOM CANONICAL BIBLE

> **READ THIS FIRST.** This is the canonical architecture + runtime-truth contract for Veklom.
> It supersedes older “Golden Bible”, agent-alignment, deployment-topology, port-doctrine, and infrastructure-constant documents wherever they conflict.
>
> **Last runtime verification:** 2026-08-09 01:42 UTC, using owner-supplied Coolify 4.1.2 screens, active Traefik dynamic configuration, proxy logs, and Sentinel logs.
> **Last repository verification:** 2026-08-09 against GitHub `main`/default branches.
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

Some Veklom-built systems are also independently sellable products. Their standalone UI is **not** embedded wholesale inside Capability OS.

Examples:

- **Project Genome Ledger / PGL** can expose its own registry, certificates, lineage, ledger, exports, and billing as a standalone product. Inside Veklom, its underlying provenance/evidence/lineage capabilities are rebuilt into Veklom-native surfaces.
- **ABIDE** can have its own standalone blueprint workbench. Inside Veklom, its blueprint/contract compilation capabilities appear as native Capability OS functions.
- The same rule applies to other reusable Veklom modules: reuse the capability/domain logic; do not paste standalone product pages into the OS.

---

## 3. Canonical Component Responsibilities

Names are implementation domains, not UI requirements.

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
| **x402** | Settlement/payment protocol integration where verified; it is not automatically proof of execution. |

### No absolute marketing claims without proof

Do **not** claim any of the following merely because code, a diagram, or a README mentions them:

- “100% production ready”
- “SOC 2 Type II compliant/certified”
- “HIPAA compliant”
- “FIPS 140-2 compliant”
- “hardware enclave protected”
- “secrets never enter software memory”
- “prompt injection eliminated”
- “immutable / impossible for admins to delete”
- sub-microsecond global quarantine
- on-chain finality

Use exact, testable language backed by current evidence.

---

## 4. Source Repositories — Current Working Set

These are the active repositories that participate directly in the current Veklom capability/runtime stack and therefore inherit this Bible:

- `reprewindai-dev/veklom-ops-command` — cross-repo operating control plane and canonical operational Bible
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
- `reprewindai-dev/apex` (standalone blueprint/product surface; capability reuse must follow the standalone-vs-OS rule above)

Historical experiments, duplicate repos, generated prototypes, and old `uacp*` variants are **not automatically canonical** because they exist. Promote a repo into this list only after source + runtime ownership are verified.

---

## 5. Operations Rules

### Coolify and GitHub

- **GitHub default branch = source truth.**
- **Coolify = deployment/runtime configuration truth.**
- Environment secrets belong in deployment secret management, not committed `.env` files.
- Do not make a direct hot patch and then leave GitHub stale. Emergency runtime fixes must be reconciled back to source.
- Do not publish credentials, tokens, private keys, or secret values in issues, docs, chat, screenshots, or logs.

### Coolify management method

- Use the **Coolify UI/API** for Coolify resource management.
- SSH is reserved for **direct host/container verification or operations** that cannot be performed safely through Coolify.
- Do not turn routine Coolify management into ad-hoc SSH editing.

### Docker networking

- `localhost` means **the current container/process namespace**.
- Inter-container traffic on the same Docker network should use the current service/container DNS name or an explicitly managed service endpoint.
- Do not hard-code ephemeral Coolify-generated container names into application source when a stable service hostname/config variable exists.

### Port rule — corrected

The old rule “port 3000 or 8000 may never be used by a public-facing service” is **false**.

Current verified routing includes services listening internally on `3000` and `8000` behind Traefik. The correct rule is:

- Internal container ports may be `3000`, `8000`, or any valid application port.
- Avoid conflicting **host-published** ports on the same host.
- Public traffic should normally enter through Traefik on `80/443` and route to the service’s internal port.
- Every route must document the actual runtime target; do not infer a port from an old Bible.

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

The owner-supplied Coolify screen reported the server reachable and validated.

### Sentinel — VERIFIED

Current configuration shown in Coolify:

- Coolify URL: `http://host.docker.internal:8000`
- metrics sampling: `10s`
- metrics history: `7 days`
- push interval: `60s`

Live Sentinel logs supplied on 2026-08-09 show repeated `200` responses from `/api/health`, periodic pushes to `/api/v1/sentinel/push`, and successful CPU/memory history queries. Treat Sentinel as operational for this verification window; re-check before making a later availability claim.

### CA certificate — VERIFIED SCREEN STATE

Coolify showed its CA certificate as valid until `2036-05-15 00:23:57` and the recommended container mount path:

`/data/coolify/ssl/coolify-ca.crt:/etc/ssl/certs/coolify-ca.crt:ro`

Only mount it where a container actually needs to trust Coolify-managed database TLS.

---

## 7. Traefik Proxy — VERIFIED + UPGRADE STATUS

### Current deployed state

Owner-provided Coolify configuration shows:

- proxy container: `coolify-proxy`
- image branch configured as `traefik:v3.6`
- actual installed version reported by Coolify: **v3.6.25**
- ports: `80:80`, `443:443`, `443:443/udp`, `8080:8080`
- Docker provider enabled
- file provider directory: `/traefik/dynamic/`
- file watch enabled
- `exposedByDefault=false`
- ACME HTTP challenge via the `http` entrypoint

### Upstream status — VERIFIED 2026-08-09

- Coolify `v4.1.2` is the current upstream Coolify release.
- Latest upstream Traefik release is **v3.7.10**.
- Deployed Traefik remains **v3.6.25**.

**Do not perform an in-place production minor upgrade simply because Coolify displays the notice.** Back up Coolify/proxy state, inspect the Traefik v3 migration guide, test the exact dynamic configuration against v3.7, and then upgrade through the supported Coolify flow.

Relevant migration behavior in the 3.7 branch includes stricter middleware/path handling in later 3.7 patch releases. The currently supplied configuration is Docker/file-provider based rather than Kubernetes, so Kubernetes-specific CRD migrations are not applicable to this host; still test all Veklom routers and middleware before cutover.

---

## 8. Active Traefik Dynamic Routes — CONFIGURED 2026-08-09

`CONFIGURED` means present in the active dynamic configuration screen. It does **not** by itself mean the upstream service is healthy.

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
| `control.veklom.com` / `app.veklom.com` | current Veklom control-plane target on `3002` in `veklom.yaml` |

There are also old `.bak` and `.disabled*` route files in the dynamic-config directory. They are historical artifacts and must not be treated as active topology. Keep backups outside the watched dynamic directory when practical.

---

## 9. KNOWN PRODUCTION ISSUE — ACME / ROOT DOMAIN ROUTING

**Open issue as of the 2026-08-09 verification window.**

Traefik logs show failed Let’s Encrypt HTTP-01 renewals for combinations of:

- `veklom.com`
- `www.veklom.com`
- `app.veklom.com`

The challenges resolve through Cloudflare addresses and return `404` from `/.well-known/acme-challenge/...`.

The dynamic configuration also contains overlapping root-domain intent (`veklom-redirect.yaml` and `veklom.yaml` both reference Veklom root/control hosts). Do not “fix” certificates by trial-and-error. First determine which origin should own each hostname, then make DNS/proxy/router ownership unambiguous and retest HTTP-01 or move to the appropriate certificate strategy.

Until resolved, do not describe root-domain certificate renewal as healthy merely because application HTTPS currently loads.

---

## 10. Data / Persistence Doctrine

- Browser frontends do not connect directly to PostgreSQL.
- Frontends call authenticated service APIs.
- Database topology is runtime configuration, not a hard-coded product assumption.
- Separate domain databases/schemas and least-privilege credentials are preferred over one unrestricted account.
- `pgvector` is a persistence capability, not a reason for every frontend/service to share direct DB access.
- Never spin up a new hosted database just because an old document says one exists or does not exist. Verify current ownership and migration requirements first.

The old July document listed specific Server 0 PostgreSQL/Redis containers and a multi-database layout. Those are now `LAST_KNOWN` until each database/resource is revalidated in current Coolify state.

---

## 11. Evidence Standard

Veklom’s evidence model must distinguish:

- **assertion** — a claim in text
- **runtime observation** — logs/UI/API output
- **persisted evidence** — durable record tied to an execution
- **cryptographically verified evidence** — signatures/hash-chain/anchor verification actually checked
- **external finality** — an independent external anchor or settlement confirmed against its authoritative system

A hash chain is **tamper-evident**. Do not automatically call it physically immutable or undeletable.

Reason-rich evidence should prefer structured fields such as:

`policy_id`, `policy_version`, `rule_id`, `jurisdiction`, `classification`, `decision`, `reason_code`, `evaluator_version`, `input_hash`, `output_hash`, `authority_grant`, `delegation_chain`, `execution_id`, and verification state.

Human-readable legal explanations may be generated from those fields, but Veklom must not fabricate legal conclusions.

---

## 12. Documentation Governance

Every participating repository must place a conspicuous link to this Bible at the top of its README and maintain a root `00_VEKLOM_BIBLE.md` mirror/pointer.

When an older document overlaps with this Bible:

1. Preserve it under `docs/archive/<date>/` when it has historical value.
2. Replace the old root file with a short deprecation pointer when agents/tools may still discover that filename.
3. Never maintain two competing “canonical” topology documents.
4. Repo-specific docs may describe local APIs/build/test behavior, but must defer cross-repo architecture, deployment ownership, and runtime topology to this Bible.

### Safe labels

Use these status words consistently:

- `VERIFIED_LIVE`
- `VERIFIED_REPO`
- `CONFIGURED`
- `LAST_KNOWN`
- `TARGET`
- `UNVERIFIED`
- `DEMO`
- `ARCHIVED`

Do not use “100% real”, “gold standard”, “production ready”, or compliance-certification language as a substitute for evidence.

---

## 13. Update Protocol

Before changing this Bible:

1. Identify the exact claim being changed.
2. Verify source truth in the relevant GitHub default branch.
3. Verify runtime truth in Coolify / the actual deployed endpoint when the claim concerns production.
4. Record the verification date and evidence type.
5. Update dependent repo mirrors/pointers.
6. Archive superseded canonical docs.
7. If runtime and source disagree, record the drift explicitly instead of choosing the more convenient story.

**The Bible is not “true because it is called the Bible.” It is canonical because every factual claim is either verified, qualified, or explicitly marked unknown.**
