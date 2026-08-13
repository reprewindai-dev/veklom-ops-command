# Veklom Recovery Handoff — 2026-08-12

Purpose: give the next coding agent a verified starting state after multiple agents confused stale task artifacts, local-only changes, merged source, and deployed production.

## Non-negotiable truth rules

1. A task checkbox is not source of truth.
2. Before implementing any planned capability, search all relevant Veklom repos and git history for an existing implementation.
3. Classify every capability separately as:
   - IMPLEMENTED_IN_REPO
   - DEPLOYED_AND_LIVE
   - FRONTEND_SURFACED
   - SPINE_JOINED
4. Never reactivate mock/demo/in-memory state to make a production UI appear functional.
5. Never claim "done" from a local file, commit, merge, or prose report. Production completion is:
   repo change -> pushed commit -> Coolify deployment -> live endpoint/UI verification -> evidence/report.
6. Existing runtime code and verified production behavior supersede stale plans and checklists.

## Verified current frontend state

Repository: `reprewindai-dev/veklom-FRONTEND`

- Current verified GitHub main contains commit `add110ac57561ffdd08e6877f24748ccf5f9696c` (`fix(cos): reconnect Mount to real CAPPO runtime (#53)`).
- `/os/mount` is an already-built Capability OS surface. Do not rebuild the UI from legacy pages.
- The new root landing page exists in `app/page.tsx`.
- The new developer portal exists in `app/dev/page.tsx`; middleware is intended to rewrite `veklom.dev /` to `/dev`.
- Production deployment of `add110a` is NOT verified. The GitHub CI job failed before runner execution and the deploy job was skipped.
- Current production behavior must therefore be treated independently from GitHub source until Coolify is verified.

### Local-only frontend change that must NOT be pushed

A local commit was reported as:

`d5c2bbc fix: un-proxy local Next.js API routes`

Its intent is to allow `app/api/v1/[...path]/route.ts` to run before the generic backend proxy. Do NOT push or deploy this change without replacing the local handler behavior first. The current local Next handler includes fabricated/demo values such as hard-coded healthy nodes, fixed CPU/memory, random x402 inputs, fake infrastructure scan results, hard-coded VNP metrics, fake PGL/Merkle claims, and fake RepoGate counts.

The commit that removed those mock Next.js backends was `36b9ca46c24b0791ba4cc4181e37387f0ddb73bc` (`Eradicate fake Next.js mock backends and wire real infrastructure`). Do not undo that security/integrity direction merely to make a screen respond.

## UCH reality: do not rebuild from the stale checklist

A local folder `C:\Users\antho\.windsurf\veklom-uch` exists. The following files were reported as newly written during the current Antigravity session, not recovered historical implementation:

- `src/proxy/mcp-interceptor.ts`
- `src/authority/cappo-client.ts`
- `src/evidence/pgl-recorder.ts`

Treat these as SCRATCH/UNTRUSTED until compared against existing runtime modules. Do not push them merely because an old task artifact showed unchecked boxes.

The substantive UCH behavior already exists across the current system, especially cAPI/Covenant:

### cAPI / Covenant

- `src/lib/covenant/mcp-bridge.ts`
  - live MCP JSON-RPC `tools/call` transport
  - mcp/http/https capability routing
  - request identity/context propagation
  - retry/timeout behavior
- `src/lib/covenant/capability-mount.ts`
  - governed capability mounts
  - execution lanes
  - grants
  - CAPPO authority requirement
  - ALLOW / DENY / HOLD / REQUIRE_APPROVAL / QUARANTINE decisions
  - trust, policy, safety and affordability checks
- `src/lib/covenant/runtime.ts`
  - governed multi-phase execution
  - Ed25519 evidence generation
  - evidence IDs, envelope hashes and signatures
  - audit/evidence handling
- `src/lib/covenant/pgl-ledger.ts`
  - PGL/GnomLedger forwarding through `/api/v1/ledger/events`

These modules mean the old UCH checklist items "MCP interceptor", "CAPPO authority", "GRANT/DENY", and "PGL recorder" cannot be treated as greenfield work. First map the existing implementation to the desired UCH boundary and identify actual gaps.

### ABIDE

ABIDE already contains capability/compiler boundary work, including:

- `src/compiler/seked.ts`
- `src/core/plan-ir.ts`
- `src/core/connectors.ts`
- `src/server/services/CovenantService.ts`
- capability graph / governed-view components

ABIDE should be inspected as the blueprint/contract compilation side of the capability lifecycle, not duplicated inside a new UCH proxy.

## Capability OS boundary

The new Capability OS is the product surface. Legacy control-plane pages are not templates to import wholesale.

Recovery pattern:

existing backend capability -> verify current route/contract -> expose inside `/os/*` -> attach identity/authority -> execute -> evidence -> measurement/settlement as applicable.

Do not use:

legacy page -> invented route -> local mock handler -> "verified" badge.

## Immediate next work order

1. Freeze Antigravity writes. Preserve its local work but make no pushes from the local `d5c2bbc` or newly-created `veklom-uch` files.
2. On the Windows machine, record exact local state for `veklom-control-plane` and `veklom-uch` using `git status`, `git log --all`, `git reflog`, and diffs. Do not clean/reset until copied into the handoff.
3. Inventory cAPI/Covenant and ABIDE against the intended UCH responsibilities before writing new UCH code.
4. Treat `veklom-FRONTEND` source and Coolify runtime separately. Determine what commit Coolify is actually running.
5. Deploy only after source build succeeds and then verify live:
   - `control.veklom.com/` serves the intended new landing page
   - `veklom.dev/` serves the intended developer portal
   - `/os` serves the new Capability OS
   - `/os/mount` calls the real CAPPO capability-mount contract
6. Only after the above is stable, continue wiring additional backend capabilities into the OS using actual current router registrations and contracts.

## Agent reporting format

For every claimed fix, report exactly:

- repository
- branch
- commit SHA
- files changed
- current route/contract used
- local tests/build result
- pushed? yes/no
- deployed to Coolify? yes/no
- live verified? yes/no
- evidence proving live behavior

If any answer is unknown, say UNKNOWN. Never substitute "should", "is deploying", or "looks correct" for verification.
