# Veklom Ops Command — Agent Manifest

> [!IMPORTANT]
> **Read [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md) first.**
> The Bible is the only cross-repository architecture/runtime/topology/port source of truth. Do not duplicate infrastructure constants in this manifest.

This file is the entrypoint for the Veklom Ops Command engineering organization. Role doctrine lives in [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md); operational non-negotiables live in [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md).

## Mandatory truth rules for every operator

- GitHub default branch is source truth.
- Coolify is deployment/runtime configuration truth.
- Live endpoint behavior is required for final production verification.
- Use Coolify UI/API/MCP for Coolify management; reserve SSH for direct host/container verification or operations.
- Never infer ports, container IDs, server placement, or service health from an old manifest.
- Host port `8000` is currently reserved by Coolify; internal Docker port `8000` may still be used behind Traefik.
- Host port `3000` must not be allocated until its present host reservation is explicitly reverified.
- No synthetic/mock evidence may be represented as production evidence.
- No secrets or private keys in Git, reports, issues, or chat.

## Engineering roles

The active engineering roles are defined in `ENGINEERING_DOCTRINE.md` and the `agents/` + `teams/` directories. Those documents define responsibilities and workflows, but any copied infrastructure fact is subordinate to `00_VEKLOM_BIBLE.md`.

## Completion rule

`repo change → pushed commit → deployed runtime → live verification → evidence/report`

If any operator cannot prove a runtime assertion, mark it `UNVERIFIED` or `LAST_KNOWN` rather than guessing.

## Historical manifest

The previous manifest, including the old Golden Bible Port Table and duplicated deployment constants, is `ARCHIVED` in Git history. See [`docs/archive/2026-08-09/README.md`](./docs/archive/2026-08-09/README.md).
