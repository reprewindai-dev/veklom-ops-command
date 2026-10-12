# Veklom Gate (Veklom Ops MCP)

> **Install:** [`deploy/INSTALL.md`](deploy/INSTALL.md) — about five minutes, read-only first.

Veklom Gate lets AI agents (Claude Code, Cursor, ChatGPT and other MCP clients) operate Docker hosts without being able to destroy them. It is intentionally **not** a generic shell and **not** a Docker administrator.

```text
agent ──MCP──▶ veklom-ops-mcp ──HTTP (internal network)──▶ docker-gate ──unix socket──▶ Docker Engine
               policy, approvals,                          the ONLY holder of the socket;
               audit, redaction                            fixed capability ceiling
```

- The MCP server decides **whether** an action may run: risk tier, live redundancy, signed approval.
- The Docker gate decides **what can run at all**: list, inspect, env-var names, log tail, restart, stop, start — on containers that opted in with a label. There is no route for exec, create, remove, attach, archive, volumes, images, networks, build or prune, so no policy bug or approval can reach them.

## Authority model

| Tier | Meaning | Default behavior |
|---|---|---|
| `LOW` | Read-only | Autonomous |
| `MEDIUM` | Reversible operational mutation | Autonomous only when observed runtime state proves it safe; otherwise approval |
| `HIGH` | Consequential mutation | One-time external approval required |
| `FORBIDDEN` | Violates a trust boundary | Never executable, even with approval |

- LOW: host info, managed-container list/inspect, env-var **names**, redacted log tail, public health probes, audit verification.
- MEDIUM: `restart_container` — autonomous in production only when at least `min_healthy_replicas` (default 2) containers of the same Compose service are running **and** passing a defined health check. A container with no health check is never counted as healthy.
- HIGH: `stop_container`, `start_stopped_container`.
- FORBIDDEN: container exec, create/remove, reading container filesystems, volume deletion, prune, raw socket access, database writes, secret-value reads/exports, arbitrary shell, disabling fail-closed/zero-trust/air-gap boundaries.

Unknown actions fail closed.

## Opting containers in

Only containers carrying the managed label are visible or actionable. Everything else — including the MCP and gate themselves, and databases you have not labelled — looks "not found":

```yaml
services:
  web:
    image: example/web:1.4.2
    labels:
      veklom.ops.managed: "true"
    healthcheck:            # required for autonomous restarts
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    deploy:
      replicas: 2           # two healthy replicas => restarts need no human
```

The label key/value is `DOCKER_GATE_MANAGED_LABEL` (default `veklom.ops.managed=true`).

## Credential separation

1. `VEKLOM_MCP_ACCESS_TOKEN` — authenticates the MCP client to the MCP server.
2. `DOCKER_GATE_READ_TOKEN` — lets the MCP call the gate's read routes only.
3. `DOCKER_GATE_ACT_TOKEN` — a different token for restart/stop/start. Startup fails if it equals the read token.
4. `DOCKER_GATE_ALLOW_ACT` — an independent switch **on the gate**. While `false` (the default), lifecycle routes return 403 whatever the MCP decides.

The MCP container never mounts the Docker socket. A compromised MCP process can therefore do at most what the gate's routes allow on labelled containers. The gate itself has no internet route (`internal: true` network) and publishes no port.

Gate responses are allowlist-projected twice (in the gate and again in the MCP). Container env values, mounts, command args, health-check output and arbitrary labels (which often carry auth hashes) never leave the gate. Logs are capped and redacted.

## Approval model — asymmetric by design

The MCP is cryptographically unable to approve its own high-risk request.

- the MCP server stores only `VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64`;
- the matching private key stays with a human or a separately trusted approval environment; list several public keys, comma-separated, to let several devices or people approve;
- each deployment has an approval **audience** (`VEKLOM_MCP_APPROVAL_AUDIENCE`, e.g. `acme-prod`); write mode refuses to start without one.

Generate a pair in the trusted approval environment:

```bash
veklom-mcp-keygen
```

When a call needs approval, the MCP returns an `approval_request` with the audience, tool, action, exact parameters, their SHA-256, and maximum TTL. The agent relays it; the approver confirms exactly what will run:

```bash
export VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64='<private-key-kept-outside-mcp>'
export VEKLOM_MCP_APPROVER_AUDIENCES='acme-prod'   # refuse to sign for any other deployment

veklom-mcp-approve --approved-by 'founder:chris' --request-json '<approval_request from the agent>'
#   You are approving exactly one call:
#     deployment : acme-prod
#     tool       : stop_container
#     action     : service.stop
#     params     : {"container":"shop-api-1"}
#   Approve? [y/N]
```

The CLI re-hashes the parameters it displays, so an agent cannot show one target and get a token for another. Explicit flags (`--tool --action --params-json --audience`) still work for scripted approvers.

### Approve from your phone

`approver/` is a static, dependency-free web app that turns a phone or laptop browser into the approval key:

1. Host it on **its own origin** (for example Cloudflare Pages: `npx wrangler pages deploy approver`). Never serve it from the MCP host: a compromised MCP could otherwise serve altered JavaScript that uses your key. The server refuses to start if `VEKLOM_MCP_APPROVER_URL` and `VEKLOM_MCP_PUBLIC_URL` share an origin.
2. Open it, enter your approver name, tap **Create signing key**. The Ed25519 key is generated by WebCrypto as **non-extractable** and kept in the browser's IndexedDB; only the public key is shown, ready to paste into `VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64`.
3. Set `VEKLOM_MCP_APPROVER_URL` and `VEKLOM_MCP_PUBLIC_URL`. Every `approval_request` now carries an `approve_url` and a `request_id`.

The flow:

```text
agent  ── stop_container ──▶ approval_required + approve_url
agent  ── wait_for_approval(request_id) … waits
human  ── opens approve_url on phone ─▶ sees exact call, fingerprint re-checked on device ─▶ holds "Approve once"
phone  ── POST /approvals/deliver (signed token) ──▶ MCP holds it for exactly that call
agent  ◀─ wait_for_approval: approved ── repeats the same call ──▶ executed (once)
```

The exact call travels in the URL **fragment**, which browsers never send to any server. The first time a deployment's link is opened, the device asks you to trust it and pins its server address; later links cannot redirect delivery elsewhere. `/approvals/deliver` needs no bearer token because only a token signed by your key is accepted, and browsers may call it only from the approver origin. A delivered approval grants nothing until the identical call is repeated, and it is still verified and consumed then. If delivery fails, the page shows the token to paste to the agent instead.

The signed (v2) token is bound to the **deployment audience, tool, action and exact parameters**, cannot exceed the server's TTL policy, expires quickly, and is consumed once. Wrong-signer tokens, audience substitution, tool/action/parameter substitution, replay, expiry, excessive TTL and legacy unbound v1 tokens are rejected. If the upstream call fails after verification, the approval is still spent and the response says so. An approval can never widen the gate: an approved stop of an unlabelled container still fails.

## Operator policy file — tighten only

`VEKLOM_MCP_POLICY_FILE` points at a JSON file that can make the built-in model stricter, never looser:

```json
{
  "forbid": ["service.stop", "infra.logs.read"],
  "require_approval": ["service.restart"],
  "min_healthy_replicas": 3
}
```

- `forbid` — any known action becomes FORBIDDEN (reads included).
- `require_approval` — medium actions lose autonomy and always need approval.
- `min_healthy_replicas` — raise the redundancy floor for autonomous production restarts (minimum 2).

There is deliberately no key to allow, downgrade or un-forbid anything. Unknown keys, unknown action names and a lowered floor fail at startup. `operations_policy` reports the effective model. See `policy.example.json`.

## Tool surface

- **Read / LOW:** `operations_policy`, `evaluate_operation`, `infrastructure_overview`, `health_matrix`, `security_posture`, `docker_host_info`, `list_containers`, `get_container`, `get_container_env_presence`, `get_container_logs`, `wait_for_approval`, `verify_mcp_audit_chain`, `recent_mcp_audit_events`, `operator_snapshot`, `render_operator_evidence_plane`.
- **MEDIUM:** `restart_container`.
- **HIGH:** `stop_container`, `start_stopped_container`.

No arbitrary command, exec, SQL or file tool exists.

## Audit evidence

Reads, denials, approval escalations, failures and completed mutations append to a local JSONL hash chain. It stores hashes of requests/results plus tool, action, tier, outcome, approver and previous hash — never raw arguments or output. Appends are serialized with a file lock.

A hash chain alone proves edits in the middle, but not deletion of the newest events or replacement of the whole file. Two defences:

- **Anchor webhook.** Set `VEKLOM_MCP_AUDIT_ANCHOR_URL` (and optionally `VEKLOM_MCP_AUDIT_ANCHOR_TOKEN`) and every event's hash, previous hash, tier and outcome is POSTed off-box as it is written.
- **Anchored verification.** `verify_mcp_audit_chain(anchor_head=...)` with a head recorded earlier outside the server fails with `anchor_not_found` if that history was truncated or replaced.

## Verification after mutations

Docker accepts a restart/stop/start before the container is healthy again. After a mutation, re-read the container (`get_container`) and the relevant public health probe before calling the change complete:

```text
request -> authorize -> mutate -> runtime re-read -> live health/proof -> evidence
```

## Configuration

Copy `.env.example`, generate the tokens, and keep real values out of Git. Read-only is the default.

To enable lifecycle actions, set **both** switches plus the approval verifier:

```text
# MCP
VEKLOM_MCP_WRITES_ENABLED=true
VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64=<public-verification-key>
VEKLOM_MCP_APPROVAL_AUDIENCE=<unique name for this deployment>
DOCKER_GATE_ACT_TOKEN=<random, different from the read token>
# gate
DOCKER_GATE_ALLOW_ACT=true
DOCKER_SOCKET_GID=<gid owning /var/run/docker.sock>
```

Set `MCP_ALLOWED_HOSTS` to the hostname clients use (for example the Cloudflare Tunnel hostname). It enables the MCP SDK's DNS-rebinding guard for exactly those hosts; without it, the SDK default would reject every non-localhost request with 421.

### Profiles and health probes

`VEKLOM_MCP_PROFILE` is `generic` by default: no vendor health targets and no security-posture endpoint. Configure your own:

```text
VEKLOM_MCP_HEALTH_TARGETS={"api":"https://api.example.com","web":{"base_url":"https://example.com","paths":["/","/status"]}}
VEKLOM_MCP_SECURITY_POSTURE_URL=https://api.example.com/security/posture   # optional
```

Veklom's own deployment sets `VEKLOM_MCP_PROFILE=veklom` to probe BYOS, CAPPO, PGL and cAPI and read the BYOS posture endpoint.

### Replica constraint

Approval nonces live on the MCP's state volume. Run **one** MCP replica per audience; otherwise a token could be consumed once per replica.

## Transport and container hardening

MCP Streamable HTTP on internal port `8787`, intended to sit behind a TLS tunnel (Cloudflare Tunnel in Veklom's Core V1). Inbound bearer auth is fail-closed; `VEKLOM_MCP_ALLOW_UNAUTHENTICATED=true` exists only for a separately authenticated private boundary.

Both containers run non-root, read-only root filesystem, all capabilities dropped, `no-new-privileges`, no published host ports. Only the gate mounts the Docker socket; only the MCP has the state volume and an outbound network. `tests/test_deployment.py` asserts these properties from the shipped compose file.

## ChatGPT / Apps SDK

The server exposes an Operator Evidence Panel as an MCP App resource. It renders managed-container counts, public health, authority settings and audit-chain state from data returned by the MCP and receives no credentials.

## Local validation

From `mcp_server/`:

```bash
python -m pip install -e '.[dev]'
pytest
```

The suite drives MCP tools through the real gate app into an in-process fake Docker Engine, including replay, substitution, unlabelled-container and secret-leak cases.

## Production rollout

1. Label the containers the agent may see; add health checks; run two or more replicas where restarts should be autonomous.
2. Deploy with `VEKLOM_MCP_WRITES_ENABLED=false` and `DOCKER_GATE_ALLOW_ACT=false`.
3. Verify `/health`, MCP initialization, tool listing, `list_containers` (only labelled containers), redacted logs, env names without values, and audit-chain verification.
4. Expose the MCP through the TLS tunnel with `MCP_ALLOWED_HOSTS` set; connect the client.
5. Generate the Ed25519 keypair outside the MCP environment; configure only the public key and a unique audience on the MCP; pin that audience in the approver's `VEKLOM_MCP_APPROVER_AUDIENCES`.
6. Enable both write switches. Verify a restart with healthy redundancy runs autonomously, a single-replica restart asks for approval, a stop refuses without approval and consumes a valid approval exactly once, and an approved stop of an unlabelled container still fails.
7. After every mutation test, re-read runtime state and health before calling it successful.
8. Confirm the MCP container has no Docker socket, approval private key, host filesystem mount, or database credential.
