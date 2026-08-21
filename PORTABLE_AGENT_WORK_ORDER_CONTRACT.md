# Veklom Portable Agent Work-Order Contract

**Purpose:** This block is mandatory context whenever a Veklom implementation plan, repair plan, work order, or architecture task is copied into an AI/IDE/agent that may not already know the Veklom repositories.

This is an **existing-system integration contract**, not a greenfield specification.

## 0. Non-negotiable repository-first rule

Before creating any file, class, service, protocol, database, ledger, policy engine, gateway, runtime, SDK, smart contract, or deployment:

1. Locate the existing canonical Veklom implementation and repository.
2. Inspect the current default branch and relevant git history.
3. Map every architecture noun in the work order to the existing component before writing code.
4. Extend, wire, migrate, or repair the existing component unless the work order explicitly marks an item `NEW / BUILD`.
5. If the canonical implementation cannot be identified with certainty, **STOP** and return `CANONICAL_COMPONENT_NOT_FOUND` with the searched repositories/paths. Do not invent a replacement.

**Architecture nouns describe existing responsibilities unless explicitly marked `NEW / BUILD`.**

Creating a parallel implementation of an existing Veklom component is a blocking failure, even if the new code has tests.

## 1. Canonical names, aliases, repositories, and ownership

| Architecture name / aliases | Canonical repository or system | Ownership | Default action |
|---|---|---|---|
| **CAPPO / cappo-backend** | `reprewindai-dev/cappo-backend` | Fail-closed runtime authorization, LAW 0, bounded execution authority / CapabilityLease issuance | **EXISTING / EXTEND OR WIRE** |
| **SEKED** | Existing Veklom policy-evaluation logic used by the governed execution path; do not manufacture a second policy authority just because a plan says “SEKED” | Policy evaluation / decision inputs to authority | **EXISTING / FIND THEN INTEGRATE** |
| **cAPI / Covenant** | `reprewindai-dev/cAPI` | Capability/API/MCP governed connection and discovery layer | **EXISTING / EXTEND OR WIRE** |
| **Gnomledger / GnomLedger / Project Genome Ledger / PGL** | `reprewindai-dev/gnomledger` | Evidence, provenance, lineage, append-only/hash-linked execution records and verification surfaces | **EXISTING / EXTEND OR WIRE** |
| **Lockerphycer** | `reprewindai-dev/lockerphycer` | Secret/key security and execution-security boundary integrations | **EXISTING / EXTEND OR WIRE** |
| **BYOS / veklom-byos-backend** | `reprewindai-dev/veklom-byos-backend` | Sovereign execution substrate/provider and execution adapters | **EXISTING / EXTEND OR WIRE** |
| **VCCP** | `reprewindai-dev/VCCP` | Capability control-plane orchestration and authority lifecycle coordination | **EXISTING / EXTEND OR WIRE** |
| **Veklom ID** | `reprewindai-dev/Veklom-ID` | Identity/trust events and identity-side verification | **EXISTING / EXTEND OR WIRE** |
| **VNP** | `reprewindai-dev/veklom-vnp` | Measurement, telemetry, routing/observation evidence | **EXISTING / EXTEND OR WIRE** |
| **RepoGate** | `reprewindai-dev/real-repo-gate-for-veklom` | Repository/capability intake and security/policy gating | **EXISTING / EXTEND OR WIRE** |
| **ABIDE** | Existing ABIDE blueprint/contract workbench. Verify the current live repository/deployment before modifying because historical `ABIDE` and `abide2` repositories both exist. | Blueprint + bounded execution-contract compilation | **EXISTING / VERIFY LIVE REPO, THEN EXTEND** |
| **x402** | Settlement rail/integration, not an authority or evidence owner | Payment/settlement only | **USE AS RAIL; DO NOT MOVE AUTHORITY INTO IT** |

### Critical alias rule

Whenever a plan mentions the evidence system, write **`GnomLedger / PGL`** (or **`Gnomledger / Project Genome Ledger / PGL`**) at first use. Never introduce `gnomledger/ledger.py`, a second “Genome Ledger,” or another local ledger implementation merely because an agent did not recognize the alias.

## 2. Responsibility separations that must not be collapsed

These are different responsibilities and must remain distinguishable in code and evidence:

- **Identity is not Policy.**
- **PolicyDecision is not CapabilityLease.** SEKED evaluates policy; CAPPO owns bounded authorization.
- **Evidence is not Permission.** GnomLedger / PGL records and verifies execution evidence; it does not grant authority merely because evidence exists.
- **Settlement is not Authority.** x402/Stripe/other rails move value after or around an authorized business consequence; payment success is not proof that an execution was authorized or correct.
- **Capability discovery is not execution authority.** cAPI can discover/connect capability surfaces; provider/tool availability does not decide Veklom authority.
- **Configured is not Authorized.** A provider, credential, route, or capability existing in configuration never expands a lease/policy scope.

## 3. Canonical consequence invariant

A consequential state change may be accepted only when the real execution path satisfies:

`AcceptedEffect => Identity ∧ Policy ∧ OperationSpecificAuthority ∧ CurrentTargetState ∧ ExecutionBoundary ∧ DurableEvidence`

Short form: **`I ∧ P ∧ A ∧ S ∧ X ∧ E`**.

The six terms are hard gates, not a weighted score.

- **I — Identity:** verified workload/human/service identity appropriate to the operation.
- **P — Policy:** current applicable policy decision and constraints.
- **A — Authority:** operation/resource-specific bounded authority (CapabilityLease or canonical equivalent).
- **S — State:** target state/version/precondition revalidated immediately before the effect.
- **X — Execution Boundary:** authority is physically enforceable at the executor/actuator/egress boundary.
- **E — Evidence:** durable post-effect evidence/receipt tied to the exact consequence.

## 4. P0 integration rule

For the current P0 consequence-authority wedge, the target is **not** to recreate all Veklom components in one new repository.

The target is to prove one real cross-repository governed consequence, currently the GitHub mutation path:

`real identity -> SEKED policy decision -> CAPPO scoped CapabilityLease -> Lockerphycer/execution boundary -> immediate target SHA/state recheck -> brokered GitHub mutation -> GnomLedger/PGL ExecutionReceipt`

Where BYOS/cAPI/VCCP participate, use their canonical implementations/contracts rather than local substitutes.

### Required adversarial gates

- valid authorized patch succeeds;
- wrong tenant/identity fails;
- missing authority fails;
- out-of-scope repo/branch/operation fails;
- stale target SHA/state fails before mutation;
- expired/replayed lease fails;
- unauthorized egress fails;
- standing production credential is not exposed to the agent/workload;
- accepted mutation produces a verifiable ExecutionReceipt.

## 5. “Done” means runtime closure, not file creation

Do not mark a task `COMPLETE`, `PRODUCTION`, `VERIFIED`, or `UNBLOCKED` merely because code and unit tests were created.

Use the following state ladder:

1. `PLANNED`
2. `IMPLEMENTED_LOCAL`
3. `COMMITTED`
4. `PUSHED`
5. `CI_VERIFIED`
6. `DEPLOYED`
7. `LIVE_VERIFIED`
8. `E2E_CONSEQUENCE_VERIFIED`
9. `INDEPENDENTLY_AUDITED` (only when true)

A production change is complete only after the relevant path reaches the required stage and the work order explicitly supplies proof.

Minimum completion evidence:

- repository name;
- branch;
- commit SHA;
- exact files changed;
- test/CI output;
- deployed runtime/version identity where applicable;
- live endpoint/action verification;
- adversarial failure evidence for security-sensitive behavior;
- post-effect receipt/evidence when the task changes consequential state.

## 6. No creative substitution on ambiguity

If the plan names a Veklom component and the agent cannot locate it, the correct behavior is **search and stop**, not “fill the missing architecture.”

Forbidden examples unless explicitly requested as new architecture:

- creating `gateway/policy/seked.py` because “SEKED” was named;
- creating `gnomledger/ledger.py` because “GnomLedger / PGL” was named;
- creating a new `lockerphycer/controller.py` outside the canonical Lockerphycer repository because execution isolation was named;
- creating a replacement CAPPO authority service inside a new gateway;
- embedding x402 settlement execution inside GnomLedger/PGL;
- creating a new Docker Compose mini-stack that duplicates CAPPO/cAPI/Lockerphycer/GnomLedger/BYOS merely to make a diagram run locally.

## 7. Required cold-agent bootstrap output before implementation

Before coding, the agent must produce a short repository mapping table like this and then proceed only when every existing component is resolved:

| Plan noun | Existing repo/path found | Existing or new? | Intended change |
|---|---|---|---|
| CAPPO | `reprewindai-dev/cappo-backend/...` | EXISTING | extend/wire |
| GnomLedger / PGL | `reprewindai-dev/gnomledger/...` | EXISTING | extend/wire |
| Lockerphycer | `reprewindai-dev/lockerphycer/...` | EXISTING | extend/wire |

If a row cannot be resolved, report `CANONICAL_COMPONENT_NOT_FOUND` and stop that row rather than inventing it.

## 8. Optimization and friction rule

Among implementations that satisfy the invariant and security/reliability constraints, prefer the path with less RAM, disk, bandwidth, recurring spend, external dependency, and operational friction. Do not introduce a second service/repository/protocol merely because it is architecturally elegant when an existing canonical component can be extended safely.

## 9. Portable work-order preamble

When a plan is pasted into another frontier model/IDE, prepend this exact short form if the full contract is not included:

> **VEKLOM EXISTING-SYSTEM RULE:** This task modifies an existing multi-repository Veklom stack; it is not greenfield. Before creating anything, map every named component to its canonical existing repository and inspect current code/history. Existing components must be extended/wired, never recreated, unless an item is explicitly marked `NEW / BUILD`. At first use write `GnomLedger / PGL` together. SEKED policy, CAPPO authority, GnomLedger/PGL evidence, Lockerphycer security, cAPI connection/discovery, BYOS execution, and x402 settlement are distinct responsibilities. If a canonical component cannot be found, stop with `CANONICAL_COMPONENT_NOT_FOUND`; do not invent a substitute. “Done” requires commit + CI/tests + deployment where applicable + live/E2E proof, not files and unit tests alone.

---

This contract supplements `00_VEKLOM_BIBLE.md`; it does not override verified runtime truth. When repository/docs/runtime disagree, follow the Bible truth hierarchy and reverify the live path.