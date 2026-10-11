# Veklom Ops MCP Security Model

This document describes the security boundary of the Veklom Ops MCP as implemented. It is a threat model, not a certification claim.

## Security objective

Provide useful machine-operated infrastructure capabilities without converting ChatGPT, an IDE, or an autonomous coding system into a standing production administrator.

The governing rule is:

```text
observe -> classify -> authorize -> act within capability -> verify -> record evidence
```

Authority is capability-scoped and risk-tiered. Unknown actions fail closed.

## Assets protected

- production availability;
- Docker Engine authority (socket access is root-equivalent on the host);
- database state;
- secrets and signing material;
- zero-trust/fail-closed controls;
- private/air-gapped service boundaries;
- deployed source/configuration integrity;
- evidence integrity;
- approval authority.

## Trust boundaries

### MCP client -> Veklom Ops MCP

The client authenticates using a dedicated MCP access credential. This credential is not a gate token and cannot be used against the Docker gate.

The MCP server validates Host/Origin when configured (and mirrors `MCP_ALLOWED_HOSTS` into the MCP SDK's DNS-rebinding guard), caps request size, and keeps public `/health` intentionally minimal.

### Veklom Ops MCP -> Docker gate

The MCP never mounts the Docker socket. It reaches Docker only through the gate over an internal network, with two credentials separated by purpose:

- read token: host info, list/inspect, env-var names, log tail;
- act token (must differ): restart, stop, start.

The gate has an independent `DOCKER_GATE_ALLOW_ACT` switch, so lifecycle actions require both the MCP's write mode and the gate's own consent.

### Docker gate -> Docker Engine

The gate is the only process holding the socket. Its capability ceiling is structural — the routes that exist — not a policy decision:

- only containers carrying the managed label are visible or actionable; unmanaged containers are indistinguishable from missing ones;
- container references are validated against a strict pattern before reaching the Engine API, and lifecycle calls use the resolved full container ID;
- there are no routes for exec, create, remove, attach, archive/export, volumes, images, networks, build, prune or env values.

Generic socket proxies filter by API section, so allowing container GETs also exposes inspect (env values) and archive/export (container filesystems). The gate exposes neither.

Responses are projected onto explicit safe fields in the gate and again in the MCP. Container env values, mounts, args, health-check output and non-allowlisted labels are never projected. Recursive secret redaction is a further layer, not the primary boundary.

Residual risk: the gate container itself holds a root-equivalent credential. Keep it minimal, on an internal network with no egress, read-only, with all capabilities dropped; review every change to `docker_gate.py` as a privileged-code change.

### Approval authority -> Veklom Ops MCP

Approval is asymmetric Ed25519.

The MCP stores only a public verification key. The private signing key remains outside the MCP service with the human/separately trusted coding-agent approval authority.

Therefore compromise of the MCP service alone does not provide the cryptographic material required to mint HIGH-risk approvals.

### MCP -> database

There is no direct SQL/query connector and no database mutation/lifecycle tool. Database writes and schema mutation are classified `FORBIDDEN`.

### MCP -> host

The MCP has no arbitrary shell tool, Docker socket, host filesystem mount, or generic command executor.

## Risk tiers

### LOW

Autonomous only for explicitly classified, non-consequential/read capabilities.

### MEDIUM

May execute autonomously only when the server derives sufficient current runtime evidence to satisfy the action's safety policy. Missing evidence causes escalation to approval.

### HIGH

Always requires an externally signed, exact-parameter, short-lived, one-time approval.

### FORBIDDEN

Cannot execute even with a valid approval token.

## Approval properties

An approval token binds:

- version (v2; unbound v1 tokens are rejected);
- nonce;
- deployment audience (`VEKLOM_MCP_APPROVAL_AUDIENCE`);
- tool name;
- canonical action name;
- SHA-256 of exact parameters;
- approver identity;
- issue time;
- expiry time.

The MCP verifies Ed25519 signature, local maximum TTL, audience, tool, action, parameters, time validity, and nonce uniqueness.

### Approver device and delivery endpoint

The browser approver (`approver/`) generates the Ed25519 key with WebCrypto as non-extractable and stores it in IndexedDB. JavaScript on the approver's origin can **use** the key but not read it out, so the approver page must be served from an origin the MCP does not control; the server refuses configuration where `VEKLOM_MCP_APPROVER_URL` shares the MCP's origin, and the page ships with a strict CSP (`script-src 'self'`, no third-party requests). Anyone who controls the approver origin can induce signatures, so treat its hosting account as a key-holder.

Approval links carry the call in the URL fragment. The page recomputes the parameter fingerprint and refuses to sign on mismatch, shows the full call, requires a deliberate press-and-hold, and delivers only to the server address pinned when the deployment was first trusted (a link cannot redirect delivery). A hostile link can therefore at most ask the human to approve something; it cannot misrepresent what is signed.

`POST /approvals/deliver` accepts unauthenticated requests by design: a body is accepted only if it carries a valid signature from the configured key, for this audience, within TTL. Browser requests are limited to the approver origin; bodies are capped at 8 KB; the inbox is bounded and entries expire with their token. Holding a delivered token grants nothing until the identical call is repeated, when it is verified and its nonce consumed exactly as a token passed directly. Every delivery attempt is audited (token hash only on rejection).

Residual risk: a lost or shared device holds a usable key. Delete it from the device (Settings › Delete signing key) and replace `VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64` on the server; old approvals stop verifying immediately.

Audience binding closes cross-deployment replay: when staging and production share an approval key, a staging approval is rejected by production even though each keeps its own nonce store. The approver CLI can pin the audiences it will sign for (`VEKLOM_MCP_APPROVER_AUDIENCES`) and re-hashes the parameters it displays, so a relayed request cannot show one target while obtaining a token for another.

Replay state uses a file lock and atomic replacement. This design is safe for a **single MCP replica**.

### Replica limitation

Do not horizontally scale the MCP approval verifier to multiple replicas while nonce state is stored locally. Before multi-replica operation, move nonce consumption to a shared atomic store or another canonical authority service with transactional uniqueness.

## Secret handling

The service deliberately does not expose:

- environment values/`real_value`;
- passwords;
- private keys;
- API tokens;
- connection strings;
- webhook/client secrets;
- unrestricted configuration bodies.

Environment inspection returns variable names/flags only.

### Text-log residual risk

Application/service logs are unstructured text. The MCP applies recursive/best-effort secret-pattern redaction and output caps, but no regex can guarantee removal of every secret an application might print in an unexpected form.

For highly sensitive workloads, disable log retrieval at the deployment/policy layer or route logs through a purpose-built sanitizer before exposing them to an MCP client.

Do not treat log redaction as a replacement for applications never logging secrets in the first place.

## Prompt injection / hostile content

Upstream logs, resource names, descriptions, deployment metadata, and application responses are untrusted data. They are not authority instructions.

The policy engine, credential scopes, approval verifier, safe-field projection, and forbidden capability set are server-side controls and must never be overridden by text found in upstream data or by a model instruction.

## Redeploy semantics

There is no redeploy, image pull or container recreate tool. Recreating a container is `docker.create_container`, which is forbidden; image changes go through the normal source → build → deploy path, not the agent.

## Evidence model

The MCP stores a local JSONL hash chain for operational calls. Entries contain metadata plus hashes of request/result rather than raw content.

This provides tamper evidence for the local ledger. On its own it does **not** detect deletion of the newest events or wholesale replacement of the file — both still produce a valid chain.

Two controls address that: `VEKLOM_MCP_AUDIT_ANCHOR_URL` streams each event hash off-box as it is written, and `verify_mcp_audit_chain(anchor_head=...)` fails with `anchor_not_found` when a head recorded outside the server is no longer in the chain. Anchoring is only as strong as the place the anchors are kept.

### Redundancy evidence

Redundancy is observed per container: the server inspects every managed container of the same Compose project/service and counts those that are running **and** whose defined health check reports `healthy`. Containers without a health check, starting, or unhealthy do not count. If the gate cannot be read, the context fails toward approval. Health checks are only as meaningful as what they test.

Future hardening may anchor MCP audit heads into Gnomledger/PGL once the exact canonical write/verification path is implemented and independently verified.

## Container boundary

Both containers run non-root, read-only, with all Linux capabilities dropped, `no-new-privileges` and no published host ports.

- MCP: no Docker socket, no host filesystem mount, no approval private key; a dedicated state volume only for approval replay state and the audit chain.
- Gate: the Docker socket and nothing else; joined only to an `internal: true` network with no outbound route.

`tests/test_deployment.py` asserts these properties against the shipped compose file.

## Residual risks

### Static inbound bearer in v1

The current deployable version uses a dedicated bearer credential at the MCP boundary. It is not yet user-scoped OAuth/OIDC. Veklom ID currently does not implement an OAuth authorization-server surface, so this implementation does not pretend otherwise.

A future OAuth issuer can replace the inbound auth adapter without changing tool policy.

### MCP process compromise

A compromised MCP process can call the gate routes its tokens allow on labelled containers — at worst restart, stop or start them — and nothing more. That is why the socket lives in the gate, why lifecycle needs the gate's own switch, and why high-risk actions also require a separate signing authority.

### Gate compromise

A compromised gate process holds the Docker socket, which is root-equivalent on the host. Mitigations are size (one small module), no egress, no published port, token-authenticated routes only, and treating `docker_gate.py` as privileged code.

### Upstream API semantic drift

Docker Engine API fields can evolve. Safe projection means new fields are not automatically exposed. Re-run the test suite and a live read-only check before upgrading Docker Engine or this client.

### Audit storage is local

Local hash-chain evidence can detect edits if verification runs against an uncompromised expected chain context, but a host-level attacker may delete the entire state volume. Independent PGL anchoring is a future defense for stronger external evidence.

## Explicit non-goals

This MCP is not:

- a root shell;
- a database administration console;
- a secrets manager UI;
- a replacement for Lockerphycer;
- a bypass around CAPPO/LAW 0 or other Veklom governance;
- proof of certification/compliance;
- proof that every upstream service is secure merely because a posture endpoint reports healthy.

## Security review gates before production write-plane enablement

1. CI green.
2. Read-only deployment verified live.
3. Gate read and act tokens verified as distinct; `DOCKER_GATE_ALLOW_ACT` deliberately enabled.
4. Only intended containers carry the managed label; `list_containers` shows nothing else.
5. Ed25519 approval keypair generated outside the MCP environment.
6. Only public approval key and a unique audience present on the MCP service.
7. HIGH action proven to reject missing/wrong/replayed approval, and an approved action on an unlabelled container proven to fail.
8. MEDIUM action proven to escalate when healthy redundancy is missing.
9. Exec, create/remove, database mutation and arbitrary shell remain absent from the MCP tool listing and the gate routes.
10. MCP container has no Docker socket, host mount, root user or approval private key; only the gate mounts the socket.
