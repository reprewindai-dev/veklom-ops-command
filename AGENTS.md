# AGENTS.md — READ FIRST

## Mandatory Capability OS continuum bootstrap

Before any Veklom implementation, review, continuation, or architecture work, read [`CURRENT_ARCHITECTURE_LOCK.md`](./CURRENT_ARCHITECTURE_LOCK.md), [`continuum/CONTINUUM_AGENT_CONTRACT.md`](./continuum/CONTINUUM_AGENT_CONTRACT.md), and [`continuum/VEKLOM_CONTINUUM_MANIFEST.json`](./continuum/VEKLOM_CONTINUUM_MANIFEST.json).

The accepted proof-and-seal continuum is the Capability OS architecture anchor. **RC1 is not accepted and is not the anchor.** Do not shrink the architecture to match a release candidate. Preserve each accepted proof at its stated scope, wire missing runtime edges into the existing canonical components, and keep CAPPO as the sole consequence authority.

Before any work in Veklom Ops Command, read [`CURRENT_ARCHITECTURE_LOCK.md`](./CURRENT_ARCHITECTURE_LOCK.md) and [`00_VEKLOM_BIBLE.md`](./00_VEKLOM_BIBLE.md).

Then read [`OPS_DOCTRINE.md`](./OPS_DOCTRINE.md), [`ENGINEERING_DOCTRINE.md`](./ENGINEERING_DOCTRINE.md), and [`AGENT_MANIFEST.md`](./AGENT_MANIFEST.md) only to the extent they do not conflict with the current architecture lock.

## Current Core V1 infrastructure lock

Current Veklom Core V1 work is restricted to owned/local hardware, Docker, Cloudflare Tunnels, GitHub source, and current Veklom services.

Do not introduce, configure, target, recover through, or treat as runtime truth:

- Coolify
- Hetzner
- Vercel
- the legacy Control Plane as the current product surface
- any Veklom subsystem/product called Headless

If an active file conflicts with this rule, stop implementation and repair/archive the stale file first.

Before implementing any planned capability, search the relevant Veklom repositories and git history for an existing implementation. Task-list checkboxes, stale implementation plans, prior model prose, archived docs, and historical deployment files are never source of truth. Existing runtime code and verified current behavior supersede them.

## Mandatory portable-work-order rule

When any Veklom implementation plan, repair plan, architecture task, or work order is copied/pasted into a frontier model, IDE automation, or coding automation that may not already have this repository context, the plan must carry the repository-first bootstrap rules with it.

At minimum, every portable work order must state:

- this is an existing multi-repository Veklom system, not a greenfield build;
- every named component must be mapped to its existing canonical repository before code is created;
- existing components are extended/wired, never recreated, unless explicitly marked `NEW / BUILD`;
- GnomLedger / PGL is the evidence system;
- CAPPO owns consequence authority; LockerPhycer owns authentication/session state; cAPI owns governed connection/discovery; VNP owns observation; ABIDE owns blueprint/contract compilation;
- if a canonical component cannot be found, return `CANONICAL_COMPONENT_NOT_FOUND` and stop instead of inventing a substitute;
- no new deployment platform, hosting provider, runtime authority, product subsystem, or topology dependency may be added without an explicit architecture decision committed to the canonical source first;
- “done” requires repository/runtime proof appropriate to the task, not merely generated files and unit tests.

## Mandatory review gate for existing work

When asked to review, verify, audit, continue, or approve another automation's work:

1. Identify exact base/head commits or branches.
2. Inspect the complete diff, including deleted, renamed, and replaced files.
3. Flag route removals, auth/middleware changes, migrations, deployment/config changes, evidence/crypto changes, and cross-repo contract changes before discussing improvements.
4. Check subsequent history for reverts/restorations/replacements.
5. Determine whether removed/restored code is canonical runtime code, legacy code, test/demo code, or fabricated/mock state.
6. Separate local-only, committed, pushed, deployed, and live-verified states. Never infer one from another.
7. Run the architecture-drift gate before approval.

A destructive or architecture-changing diff is blocking until its intent and replacement are verified.

Never reactivate demo, mock, synthetic, seeded, or in-memory state to make a production surface appear functional.
