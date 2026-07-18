# Veklom Ops Doctrine

## Objective

Make Veklom ambient, self-describing, replayable, and safe to change by coordinating specialized agent departments around observable evidence.

## System boundaries

| Layer | Truth / responsibility |
|---|---|
| GitHub main | canonical source and review history |
| Coolify / Hetzner | deployed runtime and service placement |
| Cloudflare | DNS, WAF, cache, Apex static surface |
| Poltergeist | file watching, build queue, target status, post-build checks |
| Jean / IDEs | human and agent workspaces |
| Protocol endpoints | runtime self-description |
| PGL / Gnomledger | persisted evidence and settlement records |

## Completion rule

Every release record must contain repository, branch, commit SHA, changed files, build result, test result, deployment result, HTTPS curl proof, and rollback plan. A matrix is updated only from a persisted report containing live evidence.

## Non-negotiables

- Never invent a service, port, capability, dependency, or deployment mapping.
- Never publish secrets, private IPs, SSH paths, container names, or credentials.
- Never treat synthetic or mock evidence as production evidence.
- Never use this repo as a production runtime.
- Never enable automatic production deployment from a watcher.
- Private operations matrices may contain Coolify container names, internal ports, server role notes, and deployment diagnostics.
- Public `/protocol.json` manifests must never expose container names, private IPs, secrets, environment variables, SSH paths, raw infrastructure details, or internal Docker hostnames.
- Persona anchors model leadership standards only; they do not represent real Veklom staff or endorsements.
