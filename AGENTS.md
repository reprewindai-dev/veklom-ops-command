# AGENTS.md — READ FIRST

Before any work in Veklom Ops Command, read [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md).

Then read [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md), [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md), and [`AGENT_MANIFEST.md`](./AGENT_MANIFEST.md).

If [`CODEX_RECOVERY_HANDOFF_2026-08-12.md`](./CODEX_RECOVERY_HANDOFF_2026-08-12.md) is present, read it before making any recovery, UCH, Capability OS, cAPI/Covenant, ABIDE, PGL, or deployment change.

The Bible is the sole cross-repo architecture/runtime/topology/port authority. Do not copy infrastructure constants into agent prompts or role files. Use Coolify UI/API/MCP for Coolify management; reserve SSH for direct host/container verification or operations. Host `8000` is currently Coolify-owned; internal Docker `8000` may still be used behind Traefik.

Before implementing any planned capability, search the relevant Veklom repositories and git history for an existing implementation. Task-list checkboxes, stale implementation plans, and prior agent prose are never source of truth. Existing runtime code and verified production behavior supersede them.

Never reactivate demo, mock, synthetic, seeded, or in-memory state to make a production surface appear functional. Never report work as "done" unless the pushed source is deployed to Coolify and the live behavior is independently verified.
