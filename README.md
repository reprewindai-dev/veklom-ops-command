> [!IMPORTANT]
> **VEKLOM BIBLE — READ FIRST:** [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md)
> This is the canonical cross-repo architecture/runtime-truth contract. It supersedes older topology, Golden Bible, deployment-authority, and alignment docs wherever they conflict.

# Veklom Ops Command (React SPA)

Veklom Ops Command is the standalone cross-repository operating control plane for Veklom's Poltergeist-powered DevOps teams and Capability OS continuum. This application is written in **React 19 + TypeScript + Vite + Tailwind CSS**, running on port 3000.

## Overview & Ported Features

- **Private Founder Control Cockpit**: Real-time Source Truth vs Production Truth matrix, active toolbox drill spotlight, Core Backend 4 service health, capability registry, security exposure cards, and live operator feed.
- **Interactive Command Desk Dispatcher**: Queue operational instructions with risk classification (`low`, `medium`, `high`, `critical`) and approval requirements, backed by persistent local storage.
- **Core Backend 4 Cockpit**: Live monitoring for Tier-0 backends (`veklom-byos-backend`, `cappo-backend`, `gnomledger`, `lockerphycer`) with canonical port enforcement (8088, 8002, 8001, 8092).
- **Capability Registry**: Audit and view governed tools (GitHub MCP, Poltergeist, Jean, Web MCP, Local Shell, Aiden Runner, Veklom Gate Approver).
- **The 9 Autonomous Departments**: Deep-dive into Command Desk, Poltergeist Platform, Production Truth, Release Control, Build & DevEx, Security & Secrets, Runtime Governance, Evidence & Ledger, and Edge Fleet & VNP Signals with raw JSONL report inspection.
- **Toolbox Meetings & Missions**: Explore missions (`mission-backend-purge`, `mission-001`, `mission-vanguard`, `mission-002`, `mission-capi-hardening`) with full objectives, forbidden boundaries, and department alignment matrices.
- **Veklom Gate Approver**: Authentic cryptographic device gate using WebCrypto Ed25519 non-extractable keys in IndexedDB, parameter SHA-256 fingerprint verification, 1.1s hold-to-approve single-use tokens, and device audit trail.
- **Capability OS Continuum & Architecture Lock**: Interactive explorer for `VEKLOM_CONTINUUM_MANIFEST.json`, hard invariants (`I-COMPUTE-AUTHORITY-SEPARATION`, `I-ACCEPTED-EFFECT`, `I-EVIDENCE-NOT-PERMISSION`, `I-MONOTONIC-AUTHORITY`, `I-RC1-NOT-ANCHOR`), proof programs (`P2-HOST`, `CAPPO-M1P2`, `VDB-MOBILITY-P1`, `POSTGRES-STALE-WRITER-P1`), and truth hierarchy policy.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server on port 3000
npm run dev

# Build for production
npm run build

# Run TypeScript lint verification
npm run lint
```

## Operating Truth & Invariants

- GitHub `main` is source truth.
- Runtime is owned/local hardware + Docker + Cloudflare Tunnels, per [`CURRENT_ARCHITECTURE_LOCK.md`](./CURRENT_ARCHITECTURE_LOCK.md). Coolify, Hetzner and Vercel are retired.
- CAPPO is the sole consequence authority.
- GnomLedger / PGL is the evidence domain.
- Local success is not production success.
