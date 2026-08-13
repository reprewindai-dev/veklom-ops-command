# AGENTS.md — READ FIRST

Before any work in Veklom Ops Command, read [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md).

Then read [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md), [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md), and [`AGENT_MANIFEST.md`](./AGENT_MANIFEST.md).

If [`CODEX_RECOVERY_HANDOFF_2026-08-12.md`](./CODEX_RECOVERY_HANDOFF_2026-08-12.md) is present, read it before making any recovery, UCH, Capability OS, cAPI/Covenant, ABIDE, PGL, or deployment change.

The Bible is the sole cross-repo architecture/runtime/topology/port authority. Do not copy infrastructure constants into agent prompts or role files. Use Coolify UI/API/MCP for Coolify management; reserve SSH for direct host/container verification or operations. Host `8000` is currently Coolify-owned; internal Docker `8000` may still be used behind Traefik.

Before implementing any planned capability, search the relevant Veklom repositories and git history for an existing implementation. Task-list checkboxes, stale implementation plans, and prior agent prose are never source of truth. Existing runtime code and verified production behavior supersede them.

## Mandatory review gate for existing work

When asked to review, verify, audit, continue, or approve another agent's work, do not review only the agent's prose. Perform a repository-level change audit first:

1. Identify the exact base and head commits/branches.
2. Inspect the complete diff and explicitly list deleted, renamed, and replaced files.
3. Flag large deletions, route removals, middleware/auth changes, migrations, deployment configuration changes, evidence/crypto changes, and cross-repo contract changes before discussing improvements.
4. Check subsequent history for reverts, restorations, or replacement implementations so a temporary deletion is not mistaken for permanent loss.
5. Determine whether removed/restored code is canonical runtime code, legacy code, test/demo code, or fabricated/mock state before recommending revert or reuse.
6. Separate local-only, committed, pushed, deployed, and live-verified states. Never infer one from another.

A destructive diff is a blocking review item until its architectural intent and replacement are verified.

Never reactivate demo, mock, synthetic, seeded, or in-memory state to make a production surface appear functional. Never report work as "done" unless the pushed source is deployed to Coolify and the live behavior is independently verified.
