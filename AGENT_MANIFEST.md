# Veklom Ops Command — Agent Manifest

> [!IMPORTANT]
> **Read [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md) first.**
> The Bible is the only cross-repository architecture/runtime/topology/port source of truth. Do not duplicate infrastructure constants in this manifest.

This file is the entrypoint for the Veklom Ops Command engineering organization. Role doctrine lives in [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md); operational non-negotiables live in [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md).

## Mandatory truth rules for every operator

- Read `CURRENT_ARCHITECTURE_LOCK.md` and the continuum manifest/agent contract before implementation.
- The accepted proof-and-seal continuum is the Capability OS architecture anchor; RC1 is not accepted and is downstream packaging.
- Current Core V1 infrastructure is owned/local hardware + Docker + Cloudflare Tunnels unless the architecture lock is explicitly changed.
- GitHub default branch is source truth for source; live runtime/consequence evidence governs runtime claims.
- CAPPO is the sole consequence authority. V-Chip mechanisms must integrate through CAPPO, never beside it as a second gate.
- GnomLedger / PGL owns canonical evidence/provenance/lineage closure.
- Every cross-repo task must identify the continuum invariant/program it preserves or extends.
- No synthetic/mock evidence may be represented as physical/production evidence.
- No secrets or private keys in Git, reports, issues, or chat.

## Engineering roles

The active engineering roles are defined in `ENGINEERING_DOCTRINE.md` and the `agents/` + `teams/` directories. Those documents define responsibilities and workflows, but any copied infrastructure fact is subordinate to `00_VEKLOM_BIBLE.md`.

## Completion rule

`repo change → pushed commit → deployed runtime → live verification → evidence/report`

If any operator cannot prove a runtime assertion, mark it `UNVERIFIED` or `LAST_KNOWN` rather than guessing.

## Historical manifest

The previous manifest, including the old Golden Bible Port Table and duplicated deployment constants, is `ARCHIVED` in Git history. See [`docs/archive/2026-08-09/README.md`](./docs/archive/2026-08-09/README.md).
