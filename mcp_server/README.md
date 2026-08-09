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

- LOW: health, topology, deployments, resource metadata, redacted logs, DB metadata/backups, evidence verification.
- MEDIUM: restart, same-source redeploy, cancel deployment, bounded runtime operations.
- HIGH: stop/start-after-stop, source/image/build changes, route changes, non-secret environment changes.
- FORBIDDEN: database writes/schema mutation, secret-value reads/exports, arbitrary shell, volume destruction, disabling fail-closed/zero-trust/air-gap boundaries.

Unknown actions fail closed.

## Credential separation

The service is designed around three independent credentials:

1. `VEKLOM_MCP_ACCESS_TOKEN` — authenticates the MCP client to this service.
2. `COOLIFY_READ_TOKEN` — Coolify token with `read` only. Do not grant `read:sensitive`.
3. `COOLIFY_DEPLOY_TOKEN` — separate Coolify token scoped to deployment/lifecycle operations only.

**Never provide this service a Coolify `root` token.**

The MCP never exposes upstream credentials to clients. Responses are recursively redacted before being returned or hashed into audit evidence.

## Approval model

The MCP cannot approve its own high-risk request.

For a tool call that requires approval, the server returns an `approval_request` containing:

- canonical action name;
- SHA-256 of the exact parameters;
- approval TTL.

A human or separately trusted coding-agent environment mints a one-time token outside the MCP:

```bash
veklom-mcp-approve \
  --action service.stop \
  --params-json '{"application_uuid":"..."}' \
  --approved-by 'founder:chris'
```

The token is bound to the action and exact parameters, expires quickly, and is consumed once. Parameter substitution and replay are rejected.

## Database boundary

There is **no arbitrary SQL tool** and no database mutation tool. Database capability is limited to redacted metadata and backup/status inspection. The policy engine also classifies database mutation actions as `FORBIDDEN`, providing defense in depth.

## Audit evidence

Every MCP call records a local JSONL hash-chain event. The ledger stores hashes of requests/results plus tool, action, tier, outcome, approval identity, and previous hash. It intentionally does not persist raw tool arguments or raw output.

Use:

- `verify_mcp_audit_chain`
- `recent_mcp_audit_events`

for inspection.

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
- internal port `8787` only.

## Configuration

Copy `.env.example` into Coolify's environment configuration and supply secret values through Coolify secret management. Never commit real values.

Read-only mode is the deployment default:

```text
VEKLOM_MCP_WRITES_ENABLED=false
```

After the read plane is verified, enabling lifecycle operations requires both a deploy-scoped Coolify credential and approval authority key:

```text
VEKLOM_MCP_WRITES_ENABLED=true
COOLIFY_DEPLOY_TOKEN=<deploy-only token>
VEKLOM_MCP_APPROVAL_HMAC_KEY=<random secret>
```

## ChatGPT / Apps SDK

The server exposes a Veklom Operator Evidence Panel as an MCP App resource. The widget is display-oriented: it renders structured data returned by the MCP and does not receive infrastructure credentials.

The useful operating flow is:

```text
ChatGPT
  -> Veklom Ops MCP
      -> classify authority
      -> Coolify/Veklom source-of-truth read
      -> redact
      -> hash-chain audit
      -> structured result / operator panel

State-changing request
  -> classify LOW/MEDIUM/HIGH/FORBIDDEN
  -> runtime safety evaluation
  -> external approval when required
  -> deploy-scoped upstream action
  -> verify result
  -> audit evidence
```

## Local validation

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
2. Verify `/health`, MCP initialization, tool listing, redaction tests, topology reads, Veklom health, and audit-chain verification.
3. Connect ChatGPT Developer Mode to the TLS/tunneled MCP endpoint.
4. Exercise read tools and the Operator Evidence Panel.
5. Create separate Coolify `read` and `deploy` tokens; never `root`, never `read:sensitive`.
6. Enable the lifecycle plane only after policy/approval tests are green.
7. Verify a medium-risk operation in a safe/sandbox resource before production.
8. Verify a high-risk operation refuses without an external approval and consumes a valid approval exactly once.
