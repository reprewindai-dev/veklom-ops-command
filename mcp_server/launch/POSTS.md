# Veklom Gate — launch post drafts

Drafts only. Nothing here has been posted. Before posting:

- Replace `{VIDEO_URL}` with the recorded demo (see `DEMO_SCRIPT.md`). Every post leads with it.
- Confirm the repo is public and the README on the default branch describes the Docker gate.
- Re-check every claim against the latest live run. If anything changed, change the post.
- No hype words (revolutionary, game-changing, bulletproof, unbreakable, military-grade). No user counts, stars or testimonials we don't have.
- Post from a personal account, and stay in the thread for the first few hours to answer questions.

Repo: https://github.com/reprewindai-dev/veklom-ops-command (the server lives in `mcp_server/`)

---

## Show HN

**Title** (under 80 characters):

> Show HN: Veklom Gate – let AI agents restart Docker containers but never exec or rm

**Body:**

> Demo (3 min): {VIDEO_URL}
>
> In April a coding agent found an unrelated API token and deleted a company's production database and its backups in seconds (PocketOS). Most Docker MCP servers I looked at give the agent the whole Engine API, so the same thing is one bad plan away on a Docker host.
>
> Veklom Gate is an MCP server that sits in front of Docker with a different split:
>
> - A small sidecar ("the gate") is the only process that mounts the Docker socket. It sits on an internal network with no egress and has routes for exactly seven things: list, inspect, env-var names, logs, restart, stop, start. There is no exec, create, remove, volume, image or archive route, so no prompt or policy bug can reach them.
> - Only containers labelled `veklom.ops.managed: "true"` are visible. Everything else, including your database if you don't label it, returns 404.
> - Restart is autonomous only when at least two replicas of the same Compose service are running and passing health checks. Otherwise it asks.
> - Stop/start need an Ed25519 approval signed off the server, bound to the deployment, tool and exact parameters, single use. The server only has the public key.
> - Hash-chained audit log, with an optional off-box anchor.
>
> What happened in the live run (Docker Engine 29.8, real MCP client, 2026-10-11):
>
> - restart shop-web-1 with 2 healthy replicas → executed on its own
> - restart single-replica shop-api-1 → approval_required
> - stop shop-api-1 → approval_required; with a signed approval → executed
> - replay the same approval → "Approval token has already been consumed."
> - same token on start_stopped_container shop-web-2 → "Approval token is bound to a different tool."
> - get_container on unlabelled shop-db-1 → 404
> - env presence → names like API_SIGNING_KEY, no values
> - evaluate docker.exec with approved: true → forbidden
>
> What it is not, yet: nobody runs it in production (we plan to run it on our own hosts first), there's been no external security review, inbound auth is a single bearer token, and it's one gate per Docker host. If the gate container itself is compromised, the attacker has the socket; the mitigation is keeping it tiny, non-root, read-only, with no egress and no published port. The threat model is in `mcp_server/SECURITY.md`.
>
> Signed approvals on their own aren't new; a few MCP servers do something similar. The bet is the combination for self-hosted Docker. Approvals happen on your phone through a self-hosted approver page (the signing key is a non-exportable browser key), or with a CLI.
>
> The core is open source. I'd especially like to hear from people running Compose in production: what would you need before letting an agent near it?

**First comment (post right after):**

> Quick start is in `mcp_server/README.md`: label a service, fill in `.env`, `docker compose up -d --build`. It starts read-only; lifecycle actions need two separate switches plus an approval public key. Happy to help anyone set it up on a real box.

---

## r/selfhosted

**Title:**

> I built an MCP server so Claude/Cursor can restart my Docker containers without being able to exec, delete volumes or read secrets [open source]

**Body:**

> 3-minute demo: {VIDEO_URL}
>
> I wanted to let an AI agent handle the boring 3am stuff on my Docker hosts (read logs, restart a stuck replica) without giving it the Docker socket. Every Docker MCP server I tried exposes basically the whole Engine API, and socket proxies filter by API section, which still exposes inspect env and container archive if you allow container GETs.
>
> So the setup is two containers:
>
> 1. **MCP server**: the agent talks to this. Risk tiers, approvals, audit log. It does **not** mount the Docker socket.
> 2. **Docker gate**: the only thing that mounts `/var/run/docker.sock`. Internal network, no egress, no published port, non-root, read-only. Routes for list, inspect, env-var names, logs, restart, stop, start. That's it.
>
> You opt containers in with a label:
>
> ```yaml
> labels:
>   veklom.ops.managed: "true"
> ```
>
> Unlabelled containers (your database, your Vaultwarden, whatever) just don't exist as far as the agent is concerned.
>
> Restarts run on their own only if there's another healthy replica of the same Compose service. Single-replica restarts, stops and starts need an approval you sign with a key that never sits on the server, and each approval works once, for one exact call.
>
> Tested end to end against Docker Engine 29.8 with a real MCP client. Being upfront about the limits: no production users yet, no external security review, single bearer token for auth, one gate per host. Log redaction is best effort, so you can forbid log reads in the policy file if your apps print secrets.
>
> Repo: https://github.com/reprewindai-dev/veklom-ops-command (see `mcp_server/`)
>
> Would love feedback, especially "this wouldn't work on my setup because…".

(Check r/selfhosted's current self-promotion rules on the day and follow them. Flair as appropriate.)

---

## X / LinkedIn (short)

**X:**

> An AI agent deleted a company's prod database and backups in seconds this year.
>
> I built Veklom Gate so agents can run Docker hosts without that ability: no exec/delete/volume route exists, restarts only with a healthy spare, stops need a single-use signed approval.
>
> 3-min demo: {VIDEO_URL}
> Open source: https://github.com/reprewindai-dev/veklom-ops-command

**LinkedIn:**

> Teams are starting to let AI agents near production servers. When an agent can reach a destructive API, a confused plan or a stray token is enough; one company lost its production database and backups this way in April.
>
> Veklom Gate is an open-source MCP server for Docker and Compose hosts. The agent can read logs, inspect containers and restart a replica when another healthy one is serving. It cannot exec, delete volumes or read secret values, because the only process holding the Docker socket has no route for them. Stopping a service needs a single-use approval signed with a key that never sits on the server.
>
> 3-minute demo against a real Docker Engine: {VIDEO_URL}
>
> It's early: no production users yet and no external security review. If you run Docker in production for clients or your own product, I'd like 25 minutes of your time to hear how you handle risky changes today.
>
> https://github.com/reprewindai-dev/veklom-ops-command
