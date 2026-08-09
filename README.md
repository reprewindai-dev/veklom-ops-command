> [!IMPORTANT]
> **VEKLOM BIBLE — READ FIRST:** [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md)
> This is the canonical cross-repo architecture/runtime-truth contract. It supersedes older topology, Golden Bible, deployment-authority, and alignment docs wherever they conflict.

# Veklom Ops Command

Veklom Ops Command is the standalone cross-repository operating control plane for Veklom's Poltergeist-powered DevOps teams. It gives every IDE and approved machine interface the same source-backed teams, runbooks, verification scripts, reports, release gates, and governed operational capabilities.

## Operating truth

- GitHub `main` is source truth.
- Coolify on Hetzner is runtime deployment truth.
- Cloudflare is DNS/WAF/cache and Apex static hosting only.
- Poltergeist is the local watcher, build queue, status, and evidence trigger.
- Jean, Windsurf, Cursor, VS Code, Codex, Claude Code, GitHub MCP, and Veklom Ops MCP are interchangeable interfaces only to the extent their granted capabilities permit.
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

The ops command repo governs operations across these repos; it is not embedded in any one of them.

## Nine-department team-of-teams

The canonical departments are Command Desk, Poltergeist Platform, Production Truth, Release Control, Build & DevEx, Security & Secrets, Runtime Governance, Evidence & Ledger, and Edge Fleet & VNP Signals. Each is an independent Poltergeist project with `team.md`, tool-agnostic contracts, scripts, reports, and a `poltergeist.config.json`. `scripts/start-watch-teams.sh` starts one daemon per team, while `scripts/status-watch-teams.sh` aggregates state.

Named people are persona anchors only. They do not imply employment, endorsement, or public affiliation.

Before major work, complete `runbooks/toolbox-meeting.md` and create an explicit department handoff using `standards/interdepartment-message.schema.json`.

## Founder panel

Run `./scripts/start-panel.sh` from Git Bash, `powershell -ExecutionPolicy Bypass -File .\scripts\start-panel.ps1` from Windows PowerShell, or double-click `scripts/start-panel.cmd`. Then open `http://127.0.0.1:4173`. The private panel reads this repository's version, branch, commit, canonical team configs, reports, and change state. Its Command Desk message box appends approval-gated instructions to `reports/command-desk-inbox.jsonl` for the operating team to process.

The actual department execution layer is `runner/runner.mjs`. Configure an approved model/API key and run `scripts/run-agent-mission.ps1`; without those credentials the runner refuses to execute and does not fabricate reports.

Continuous operation is defined in `AUTONOMY_DOCTRINE.md` and started with `scripts/start-agent-watch.ps1`.

## Veklom Ops MCP

`mcp_server/` is the machine-facing operations and evidence plane. It is **not** a generic shell and it is **not** an unrestricted production administrator.

Its authority model is:

- **LOW** — autonomous when the capability is read-only or explicitly classified as safe.
- **MEDIUM** — runtime-evaluated; autonomous only when guardrails prove the action safe, otherwise approval is required.
- **HIGH** — explicit, one-time external approval is required.
- **FORBIDDEN** — never executable, including with approval.

Database writes, arbitrary shell, secret-value export, zero-trust bypass, fail-closed disablement, air-gap removal, destructive volume operations, and equivalent trust-boundary violations are forbidden capabilities rather than merely high-risk actions.

See [`mcp_server/README.md`](./mcp_server/README.md) for the tool, credential, audit, Apps SDK, and deployment design.

## Safe start

```bash
./scripts/verify-repo-structure.sh
./scripts/status-watch-teams.sh
```

To enable watchers, install Poltergeist and Watchman using the upstream instructions, then run `./scripts/start-watch-teams.sh`. Watchers do not gain production authority merely by running; all consequential operations remain subject to capability policy.

## Scope boundary

This repository can **observe, verify, diagnose, correct, deploy, and operate** when the requested action is inside an explicitly granted capability and passes the risk policy. It never grants standing unrestricted production access.

The invariant is:

`observe → classify → authorize → act within scope → verify → record evidence`

When runtime facts are missing, risk classification fails toward approval. When an action violates a non-bypassable trust boundary, it is denied regardless of who requests it.
