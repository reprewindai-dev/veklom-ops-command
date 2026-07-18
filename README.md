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

## Nine-department team-of-teams

The canonical departments are Command Desk, Poltergeist Platform, Production Truth, Release Control, Build & DevEx, Security & Secrets, Runtime Governance, Evidence & Ledger, and Edge Fleet & VNP Signals. Each is an independent Poltergeist project with `team.md`, tool-agnostic agent contracts, scripts, reports, and a `poltergeist.config.json`. `scripts/start-watch-teams.sh` starts one daemon per team, while `scripts/status-watch-teams.sh` aggregates state.

Named people are persona anchors only. They do not imply employment, endorsement, or public affiliation.

Before major work, complete `runbooks/toolbox-meeting.md` and create an explicit department handoff using `standards/interdepartment-message.schema.json`.

## Founder panel

Run `./scripts/start-panel.sh` from Git Bash, `powershell -ExecutionPolicy Bypass -File .\scripts\start-panel.ps1` from Windows PowerShell, or double-click `scripts/start-panel.cmd`. Then open `http://127.0.0.1:4173`. The private panel reads this repository's version, branch, commit, canonical team configs, reports, and change state. Its Command Desk message box appends approval-gated instructions to `reports/command-desk-inbox.jsonl` for the operating team to process.

## Safe start

```bash
./scripts/verify-repo-structure.sh
./scripts/status-watch-teams.sh
```

To enable watchers, install Poltergeist and Watchman using the upstream instructions, then run `./scripts/start-watch-teams.sh`. The configs intentionally do not auto-deploy or mutate production.

## Scope boundary

This repository observes, verifies, records, and gates. It does not SSH into production, patch running containers, rotate credentials, or deploy services.
