# Veklom Ops MCP

Veklom Ops MCP is the governed machine-facing operations plane for Veklom infrastructure. It is intentionally **not** a generic shell and **not** an unrestricted Coolify administrator.

It provides ChatGPT and other MCP clients with source-backed operational capabilities while enforcing Veklom's least-authority model at the server boundary.

## Authority model

Every operation is classified before execution:

| Tier | Meaning | Default behavior |
|---|---|---|
| `LOW` | Read-only or demonstrably non-consequential | Autonomous |
| `MEDIUM` | Reversible operational mutation | Autonomous only when runtime guardrails prove it safe; otherwise approval |
| `HIGH` | Consequential production/configuration mutation | One-time external approval required |
| `FORBIDDEN` | Violates a trust/security boundary | Never executable, even with approval |

Examples:

- LOW: health, topology, domains, deployments, resource metadata, env-name presence, redacted logs, DB metadata/backups, evidence verification.
- MEDIUM: application/service restart, exact-artifact redeploy when independently proven, deployment cancellation, bounded runtime operations.
- HIGH: stop/start-after-stop, source/image/build changes, route changes, non-secret environment changes.
- FORBIDDEN: database writes/schema mutation, secret-value reads/exports, arbitrary shell, volume destruction, disabling fail-closed/zero-trust/air-gap boundaries.

Unknown actions fail closed.

## Coolify credential separation

The service uses purpose-separated credentials:

1. `VEKLOM_MCP_ACCESS_TOKEN` — authenticates the MCP client to this service.
2. `COOLIFY_READ_TOKEN` — Coolify token with `read` only. Do not grant `read:sensitive`.
3. `COOLIFY_DEPLOY_TOKEN` — separate Coolify token with `deploy` only for lifecycle/deployment operations.

The current Coolify `v4.x` API routes require `deploy` for application/service start, restart, stop, `/deploy`, and deployment cancellation, so this MCP does **not** need a Coolify `write` or `root` credential for its operational lifecycle tools.

**Never provide this service a Coolify `root` token. Never mount a Coolify `write` token just to make an operation easier.**

The MCP never exposes upstream credentials to clients. Resource responses are first projected onto explicit safe fields and then recursively redacted. A new upstream field is invisible until it is deliberately added to a safe projection.

## Environment-variable presence without values

`get_application_env_presence` returns variable names and non-secret flags only. It structurally discards `value` and `real_value` before a result can leave the server.

That lets an operator answer “is `COVENANT_EVIDENCE_SIGNING_KEY` configured?” without ever reading the key.

## Approval model — asymmetric by design

The MCP is cryptographically unable to approve its own high-risk request.

Approval uses **Ed25519**:

- the MCP server stores only `VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64`;
- the matching `VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64` stays outside the MCP server with the founder or a separately trusted coding-agent approval environment;
- the server has a verifier but no signing method/key.

Generate a pair in the trusted approval environment:

```bash
veklom-mcp-keygen
```

Store only the generated public key in Coolify for the MCP service. Store the private key in the separate approval environment/secret store.

When a tool call needs approval, the MCP returns an `approval_request` containing the canonical action, SHA-256 of the exact parameters, and maximum TTL.

The external approver mints a one-time token:

```bash
export VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64='<private-key-kept-outside-mcp>'

veklom-mcp-approve \
  --action service.stop \
  --params-json '{"application_uuid":"..."}' \
  --approved-by 'founder:chris'
```

The signed token is bound to the action and exact parameters, cannot exceed the server's TTL policy, expires quickly, and is consumed once. Wrong-signer tokens, parameter substitution, action substitution, replay, expiry, and excessive TTL are rejected.

## Database boundary

There is **no arbitrary SQL tool** and no database mutation/lifecycle tool. Database capability is limited to safe-projected metadata and backup/status inspection. The policy engine also classifies database mutation actions as `FORBIDDEN`, providing defense in depth.

The MCP does not expose database start/stop/restart, backup creation/restore/trigger, schema mutation, credentials, connection strings, or direct query execution.

## Current tool surface

### Read / LOW

- operations policy + operation classification
- infrastructure overview
- Veklom health matrix
- Veklom security posture
- server list/details/resources/domains
- application list/details/env-name presence/log tail
- database list/details/backup metadata
- service list/details/log tail
- deployment list/details
- MCP audit-chain verify/tail
- source-backed Operator Evidence Panel

### MEDIUM / conditional

- application restart
- service-stack restart
- normal application redeploy (currently escalates unless exact artifact identity is independently proven)
- deployment cancellation

### HIGH / approval

- stop application
- start deliberately stopped application
- stop service stack
- start deliberately stopped service stack

No arbitrary command tool exists.

## Audit evidence

Governed upstream operational reads/writes, denials, approval escalations, failures, and completed mutations record local JSONL hash-chain events. The ledger stores hashes of requests/results plus tool, action, tier, outcome, approval identity, and previous hash. It intentionally does not persist raw tool arguments or raw output.

Pure introspection tools such as `operations_policy`, `verify_mcp_audit_chain`, and `recent_mcp_audit_events` do not mutate the chain they are inspecting. The Operator Evidence Panel also reads the current chain state rather than adding an event merely because it was rendered.

Use:

- `verify_mcp_audit_chain`
- `recent_mcp_audit_events`

for inspection.

## Verification after mutations

Coolify lifecycle operations can be asynchronous. A successful POST response means the operation was accepted/executed by the upstream API; it is **not automatically proof that the resulting production state is healthy**.

After a mutation, the operator/client must re-read the affected application/service/deployment and, where relevant, the public health endpoint before calling the change complete. The canonical completion rule remains:

```text
request -> authorize -> mutate -> runtime re-read -> live health/proof -> evidence
```

## Transport

The server uses MCP Streamable HTTP and is intended to sit behind an approved TLS/private-tunnel boundary. The container listens only on internal port `8787`; the included Compose file does not publish a host port.

Inbound bearer authentication is fail-closed by default. `VEKLOM_MCP_ALLOW_UNAUTHENTICATED=true` exists only for a separately authenticated private/tunneled boundary and should not be used on a public endpoint.

## Container hardening

The included deployment runs:

- non-root user;
- read-only root filesystem;
- all Linux capabilities dropped;
- `no-new-privileges`;
- no Docker socket;
- no host filesystem mount;
- only a small persistent state volume for approval nonces and audit hashes;
- internal port `8787` only;
- approval **public key only** — never the signing private key.

## Configuration

Copy `.env.example` into Coolify's environment configuration and supply secret values through Coolify secret management. Never commit real values.

Read-only mode is the deployment default:

```text
VEKLOM_MCP_WRITES_ENABLED=false
```

After the read plane is verified, enabling lifecycle operations requires a deploy-scoped Coolify credential plus the Ed25519 **public** approval key:

```text
VEKLOM_MCP_WRITES_ENABLED=true
COOLIFY_DEPLOY_TOKEN=<deploy-only token>
VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64=<public-verification-key>
```

Do **not** add the approval private key to the MCP service.

## ChatGPT / Apps SDK

The server exposes a Veklom Operator Evidence Panel as an MCP App resource. The widget is display-oriented: it renders structured data returned by the MCP and does not receive infrastructure credentials.

The useful operating flow is:

```text
ChatGPT
  -> Veklom Ops MCP
      -> classify authority
      -> Coolify/Veklom source-of-truth read
      -> safe-field projection
      -> redact
      -> operational audit evidence
      -> structured result / operator panel

State-changing request
  -> classify LOW/MEDIUM/HIGH/FORBIDDEN
  -> derive runtime safety facts
  -> external Ed25519 approval when required
  -> deploy-scoped upstream action
  -> re-read runtime/live health
  -> record/inspect evidence
```

## Local validation

From `mcp_server/`:

```bash
python -m pip install -e '.[dev]'
pytest
```

For development only, set a dummy inbound token before importing the ASGI app:

```bash
export VEKLOM_MCP_ACCESS_TOKEN=local-test-token
uvicorn veklom_ops_mcp.main:app --host 127.0.0.1 --port 8787
```

Then connect an MCP inspector to `http://127.0.0.1:8787/mcp` using the same bearer token.

## Production rollout

1. Deploy with `VEKLOM_MCP_WRITES_ENABLED=false`.
2. Verify `/health`, MCP initialization, tool listing, safe projections, redaction tests, topology reads, Veklom health, and audit-chain verification.
3. Connect ChatGPT Developer Mode to the TLS/tunneled MCP endpoint.
4. Exercise read tools and the Operator Evidence Panel.
5. Create separate Coolify `read` and `deploy` tokens; never `root`, never `write`, never `read:sensitive` unless a future reviewed capability explicitly proves it is required.
6. Generate the Ed25519 approval keypair outside the MCP environment; configure only the public key on the MCP.
7. Enable the lifecycle plane only after policy/approval tests are green.
8. Verify a medium-risk operation in a safe/sandbox resource before production.
9. Verify a high-risk operation refuses without an externally signed approval and consumes a valid approval exactly once.
10. After every mutation test, re-read runtime state and health before calling it successful.
11. Confirm the MCP container has no approval private key, Docker socket, host filesystem mount, database mutation credential, or arbitrary shell capability.
