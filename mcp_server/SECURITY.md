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
- Coolify control-plane authority;
- database state;
- secrets and signing material;
- zero-trust/fail-closed controls;
- private/air-gapped service boundaries;
- deployed source/configuration integrity;
- evidence integrity;
- approval authority.

## Trust boundaries

### MCP client -> Veklom Ops MCP

The client authenticates using a dedicated MCP access credential. This credential is not a Coolify token and cannot be reused directly against Coolify.

The MCP server validates Host/Origin when configured, caps request size, and keeps public `/health` intentionally minimal.

### Veklom Ops MCP -> Coolify

Two credentials are separated by purpose:

- `read` only;
- `deploy` only.

The MCP is not configured with Coolify `write`, `read:sensitive`, or `root` for its current capabilities.

Read responses are projected onto explicit safe fields before returning to the MCP client. Recursive secret redaction is a second defensive layer, not the primary permission boundary.

### Approval authority -> Veklom Ops MCP

Approval is asymmetric Ed25519.

The MCP stores only a public verification key. The private signing key remains outside the MCP service with the human/separately trusted coding-agent approval authority.

Therefore compromise of the MCP service alone does not provide the cryptographic material required to mint HIGH-risk approvals.

### MCP -> database

There is no direct SQL/query connector and no database mutation/lifecycle tool. Database writes and schema mutation are classified `FORBIDDEN`.

### MCP -> host

There is no arbitrary shell tool, Docker socket, host filesystem mount, or generic command executor.

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

- version;
- nonce;
- canonical action name;
- SHA-256 of exact parameters;
- approver identity;
- issue time;
- expiry time.

The MCP verifies Ed25519 signature, local maximum TTL, action, parameters, time validity, and nonce uniqueness.

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

A normal redeploy from a configured Git branch can deploy a newer commit. Therefore “same source configuration” is not proof of “same artifact.”

Autonomous `service.redeploy_same_commit` requires independent exact-artifact verification. Until that proof exists in runtime context, the action escalates to approval.

## Evidence model

The MCP stores a local JSONL hash chain for operational calls. Entries contain metadata plus hashes of request/result rather than raw content.

This provides tamper evidence for the local ledger. It does **not** by itself prove physical immutability, independent anchoring, or external finality.

Future hardening may anchor MCP audit heads into Gnomledger/PGL once the exact canonical write/verification path is implemented and independently verified.

## Container boundary

The production container is designed to run:

- non-root;
- read-only filesystem;
- all Linux capabilities dropped;
- `no-new-privileges`;
- no host port publication in Compose;
- no Docker socket;
- no host filesystem mount;
- no approval private key;
- a dedicated state volume only for approval replay state/audit chain.

## Residual risks

### Static inbound bearer in v1

The current deployable version uses a dedicated bearer credential at the MCP boundary. It is not yet user-scoped OAuth/OIDC. Veklom ID currently does not implement an OAuth authorization-server surface, so this implementation does not pretend otherwise.

A future OAuth issuer can replace the inbound auth adapter without changing tool policy.

### MCP process compromise

A compromised MCP process can exercise whatever the configured Coolify `read` and `deploy` credentials permit. That is why this service deliberately excludes `write`, `read:sensitive`, and `root`, and why high-risk actions also require a separate signing authority.

### Upstream API semantic drift

Coolify API response fields/routes can evolve. Safe projection means new response fields are not automatically exposed. CI and periodic contract verification should re-check current routes/permissions before upgrading Coolify or this client.

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
3. Coolify `read` token verified without `read:sensitive`.
4. Coolify `deploy` token verified as a distinct credential.
5. Ed25519 approval keypair generated outside the MCP environment.
6. Only public approval key present on the MCP service.
7. HIGH action proven to reject missing/wrong/replayed approval.
8. MEDIUM action proven to escalate when required runtime facts are missing.
9. Database mutation and arbitrary shell remain absent from MCP tool listing.
10. Container has no Docker socket, host mount, root user, approval private key, Coolify `write`, or Coolify `root` credential.
