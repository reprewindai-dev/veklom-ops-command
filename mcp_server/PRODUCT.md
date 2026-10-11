# Veklom Ops MCP — product brief

Status: pre-revenue. Verified end to end against a real Docker Engine (29.8) on 2026-10-11; no production user yet, including Veklom. Market research as of 2026-10-10/11; items marked *unverified* could not be confirmed from a primary source.

Target platform: **plain Docker / Docker Compose hosts** — the same platform as Veklom's Core V1 (owned hardware + Docker + Cloudflare Tunnels, per `CURRENT_ARCHITECTURE_LOCK.md`), so Veklom can be the first production user of its own product.

## One line

Let AI agents run your Docker servers at 3am — read logs, restart a sick replica — without ever being able to exec into, delete or reconfigure anything, and with approvals the agent cannot forge.

## The problem buyers already feel

- **April 2026, PocketOS:** a Cursor agent running Claude found an unrelated Railway API token and called `volumeDelete`, wiping the production database and backups in seconds ([Euronews](https://www.euronews.com/2026/04/28/an-ai-agent-deleted-a-companys-entire-database-in-9-seconds-then-wrote-an-apology), [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/claude-powered-ai-coding-agent-deletes-entire-company-database-in-9-seconds-backups-zapped-after-cursor-tool-powered-by-anthropics-claude-goes-rogue)).
- **July 2025, Replit/SaaStr:** an agent deleted a production database during a code freeze ([eWeek](https://www.eweek.com/news/replit-ai-coding-assistant-failure/)).
- **Gravitee, Feb 2026 (n>900):** 88% of organizations report confirmed or suspected agent security incidents ([report](https://www.gravitee.io/blog/state-of-ai-agent-security-2026-report-when-adoption-outpaces-control)).

Here, volume deletion is not a forbidden *policy* — there is no code path that can reach it. The agent never holds the Docker socket.

## What is actually different

Most Docker MCP servers hand the agent the whole Engine API:

| | This server | Popular Docker MCP servers (ckreiling/mcp-server-docker ~746★, QuantGeekDev/docker-mcp ~504★, Swartdraak, alisaitteke…) | Docker socket proxies (Tecnativa ~2.8k★, linuxserver, wollomatic) | Generic MCP gateways (Preloop, PolicyLayer, Runlayer…) |
|---|---|---|---|---|
| Exec / create / remove / volumes | No route exists | Exposed | Allowed per API section | Depends on wrapped server |
| Env values / container filesystems | Never leave the gate | Exposed | Container GET exposes inspect env and archive/export *(reported as CVE-2026-78122)* | Depends |
| Scope | Opt-in label per container | Whole host | Whole host | Tool names |
| Restart autonomy from live health | Only with ≥2 healthy replicas of the Compose service | No | No | No |
| Approval the agent cannot forge | Ed25519, minted off-box, bound to deployment + tool + exact params, single-use | None / prompt-level plan-then-apply | n/a | Click in Slack/console |
| Tamper-evident audit | Hash chain + off-box anchor + anchored verify | No | No | Varies |

Sources: [ckreiling](https://github.com/ckreiling/mcp-server-docker), [QuantGeekDev](https://github.com/QuantGeekDev/docker-mcp), [Tecnativa](https://github.com/Tecnativa/docker-socket-proxy), [CVE write-up (VulnCheck)](https://www.vulncheck.com/advisories/docker-socket-proxy-through-insufficient-access-control-granularity-exposes-container-filesystems), [wollomatic](https://github.com/wollomatic/socket-proxy), [Portainer MCP](https://github.com/portainer/portainer-mcp), [Preloop pricing](https://preloop.ai/pricing), [Runlayer funding](https://fintech.global/2026/06/26/runlayer-raises-30m-to-make-every-employee-ai-native/).

**Honest positioning:** signed approvals alone are not novel — a Kubernetes MCP server (ocm-mcp-server, *partly verified*) and a paid service (LoopPause) describe Ed25519-signed approvals, and ops-copilot-mcp has a server-minted one-time confirm token. The differentiated claim is the **combination**: a socket-holding capability gate with label scoping + approvals minted outside the agent + redundancy-aware autonomy, for self-hosted Docker. Portainer, the incumbent with a paid product, has marked its own MCP server unsupported.

## Who buys first

1. **Agencies and freelancers operating many client Docker hosts.** Routine ops across many boxes, a need to show clients who did what, and one approval audience per client host. Highest willingness to pay among self-hosters.
2. **Small product teams running Compose on their own servers who already use Claude Code or Cursor.** Large audience (r/selfhosted ~500–640k members, *unverified*), low budget: the free tier and the funnel.
3. **Later:** teams behind Teleport/Runlayer/Preloop who want an infrastructure-aware layer behind their gateway. Complementary, not competing.

## Packaging and pricing hypothesis

Benchmarks: Preloop $12–350/mo cloud, $6k/yr self-hosted business; Infisical $20–40 per identity/mo; StrongDM ~$50/user/mo *(third-party)*; Teleport ~$12–18 per resource/mo *(unverified)*.

| Tier | Price (hypothesis) | What is in it |
|---|---|---|
| Open source | Free | Everything in this repo: gate, tiers, forbidden floor, signed single-use approvals, CLI approver, hash-chain audit, tighten-only policy |
| Team | $29 per protected host / month, or $149/mo up to 10 | Approval inbox (web + phone push, one-tap approve with the signing key in the approver's own passkey/secure enclave — never held by us), multi-approver quorum for chosen actions, hosted audit anchor with retention and export, policy packs |
| Agency | $399/mo up to 50 hosts | Team + per-client audit reports and approver groups |
| Enterprise | Quote | OAuth/OIDC inbound auth, shared nonce store for HA, Kubernetes adapter, SLA |

The paid line is the **approval experience and the evidence**, not the safety core. Keeping the core open is what makes the security claims credible.

## What has to be true before charging anyone

1. **Approval UX is a command-line tool.** Nobody pays to paste JSON into a terminal at 3am. The approval inbox is the product.
2. **No production user yet.** Veklom's own Core V1 hosts are the natural first deployment; nobody outside Veklom has run it, and there has been no external security review of the gate.
3. **Inbound auth is a single static bearer token.** Fine for one operator; not for a team.
4. **One MCP replica per deployment**, because approval nonces live on the local volume.
5. **Single host per deployment.** One gate per Docker host; multi-host fleets need one stack per host or a gate-per-host fan-out.
6. **Branding.** Package, env vars and docs are named for Veklom's internal platform. Pick a product name before public launch.

## Two-week validation plan

1. Run it on Veklom's own Core V1 Docker hosts first; that is the reference deployment and the demo environment.
2. Record a 3-minute video: the agent tries the PocketOS sequence (exec, delete a volume) and there is no way to do it; restarts one of two healthy replicas on its own; asks to stop a service and gets it only after a human approves; tries to reuse the approval and is refused.
3. Post to r/selfhosted, Show HN and Docker community channels, leading with the video.
4. Book 15 conversations with agencies and small teams running Compose in production. Ask what their agent has broken, who approves risky changes today, and what they pay for adjacent tools.
5. **Pass bar:** 5 people run it against real servers, and 3 agree to pay for the approval inbox (pre-sale or letter of intent). Below that, change the wedge before building the paid tier.

## Build order after validation

1. Approval inbox (web + push) with passkey-held signing keys.
2. Hosted audit anchor endpoint (the server already streams to `VEKLOM_MCP_AUDIT_ANCHOR_URL`).
3. Multi-host: one gate per host behind one MCP, with per-host audiences.
4. OAuth/OIDC inbound auth and a shared nonce store for HA.
