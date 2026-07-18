# Command Router

| Request signal | Owning captain | Required handoffs |
|---|---|---|
| 502/503/504, health, Traefik, container, domain | Production SRE | Security for exposure; Evidence for report |
| protocol.json, introspect, capabilities, links | Protocol Mesh | SRE for live proof; Release for rebuild proof |
| secret, token, password, firewall, port, onboarding | Security Secrets | Release if a change is required |
| branch, commit, PR, deploy, rollback, release | Release Manager | Security and SRE gates |
| IDE task, Jean, watcher, build, agent prompt | Build/IDE | Release before merge |
| Hetzner, region, probe, failover, floating IP | Edge Fleet | Security and SRE |
| Portal, Apex, Terminal, GPC, product surface | Product Runtime | Protocol Mesh and Release |
| PGL, Gnomledger, settlement, permit, retrieval proof | Evidence Proof | Protocol Mesh and Release |

## Canonical departments

Command Desk routes. Poltergeist Platform owns watcher discipline. Production Truth owns live claims. Release Control owns source-to-deploy proof. Build & DevEx owns local work. Security & Secrets has veto power over exposure. Runtime Governance owns Cappo/cAPI enforcement. Evidence & Ledger owns persisted proof. Edge Fleet & VNP Signals owns regional probes and scoring.

## Execution sequence

```text
Chris command → router → captain → sub-agent checks → release gate → security gate
→ GitHub main → Coolify → live HTTPS proof → evidence report → matrix update
```

No captain may self-approve a production release. Build/IDE agents may prepare changes; only Release Manager can declare release readiness after required evidence exists.
