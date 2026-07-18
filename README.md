# Veklom Ops Command

Veklom Ops Command is the standalone cross-repository operating control plane for Veklom's Poltergeist-powered DevOps agent teams. It gives every IDE the same source-backed teams, runbooks, verification scripts, reports, and release gates.

## Operating truth

- GitHub `main` is source truth.
- Coolify on Hetzner is runtime deployment truth.
- Cloudflare is DNS/WAF/cache and Apex static hosting only.
- Poltergeist is the local watcher, build queue, status, and evidence trigger.
- Jean, Windsurf, Cursor, VS Code, Codex, Claude Code, and GitHub MCP are interchangeable interfaces.
- Local success is not production success.
- A change is complete only after repo-backed change → pushed commit → Coolify deployment → live HTTPS proof.
- Hot patches are emergency-only and must be reconciled back into GitHub.
- No secrets belong in Git, chat, scripts, configs, or reports.

## Core Backend 4

These are Tier 0 and receive the strictest gates:

1. `veklom-byos-backend`
2. `cappo-backend`
3. `gnomledger`
4. `lockerphycer`

The ops command repo watches these repos; it is not embedded in any one of them.

## Team-of-teams

Each team is an independent Poltergeist project with `team.md`, tool-agnostic agent contracts, scripts, reports, and a `poltergeist.config.json`. `scripts/start-watch-teams.sh` starts one daemon per team, while `scripts/status-watch-teams.sh` aggregates state.

## Safe start

```bash
./scripts/verify-repo-structure.sh
./scripts/status-watch-teams.sh
```

To enable watchers, install Poltergeist and Watchman using the upstream instructions, then run `./scripts/start-watch-teams.sh`. The configs intentionally do not auto-deploy or mutate production.

## Scope boundary

This repository observes, verifies, records, and gates. It does not SSH into production, patch running containers, rotate credentials, or deploy services.

