# Capability OS Continuum Agent Contract

## Purpose

This contract is mandatory for Codex, Antigravity, IDE automation, reviewers, and any other coding automation working on Veklom.

The **accepted Veklom proof-and-seal continuum is the architecture anchor**. RC1 is not accepted and is not the anchor. A release candidate must conform to the continuum; it may not redefine the system downward.

Machine-readable source: [VEKLOM_CONTINUUM_MANIFEST.json](./VEKLOM_CONTINUUM_MANIFEST.json).

## Bootstrap order

Before implementation:

1. Read `CURRENT_ARCHITECTURE_LOCK.md`.
2. Read this contract and `continuum/VEKLOM_CONTINUUM_MANIFEST.json`.
3. Read `00_VEKLOM_BIBLE.md`.
4. Resolve every named component to its canonical repository.
5. Map the requested change to the continuum invariant(s) and proof program(s) it must preserve.

If a canonical component cannot be found, return `CANONICAL_COMPONENT_NOT_FOUND` and stop instead of manufacturing a substitute.

## Non-negotiable architecture

- **CAPPO is the sole consequence authority.**
- **GnomLedger / PGL owns canonical evidence/provenance/lineage closure.**
- LockerPhycer / Veklom ID own their identity/secret domains.
- cAPI / Covenant owns governed connection/discovery.
- VCCP / UCH / UCR own capability lifecycle/orchestration.
- ABIDE owns blueprint/contract compilation.
- VNP owns observation/measurement.
- V-Chip supplies authority-lineage/falsification mechanisms; it must not become a second ALLOW/DENY service.
- The four-file `virtualdb-stub` in `vchip-lab` is not VirtualDB. Do not build against it as if it were the canonical implementation.

## Core invariant

`computational_possession != current_consequence_authority`

A workload may possess code, copied state, runtime material, or historical credentials and still be unable to cause the next governed consequence when its authority is stale, revoked, out of scope, or bound to another incarnation.

For accepted effects:

`AcceptedEffect => Identity ∧ Policy ∧ OperationSpecificAuthority ∧ CurrentTargetState ∧ ExecutionBoundary ∧ DurableEvidence`

Evidence is not permission.

## Proof-preservation rule

Do not downscope an accepted proof because the current release candidate is missing the corresponding wiring.

Instead:

1. identify the missing integration edge;
2. extend/wire the existing canonical component;
3. add the hostile/contract test that makes the invariant executable;
4. bind the resulting runtime evidence into PGL;
5. preserve the original proof scope and its explicit boundaries.

Likewise, do not inflate a bounded proof into a universal claim. The manifest stores both the accepted program status and its tested boundary.

## Required PR/work-order fields

Every cross-repo implementation PR or portable work order must state:

- **Continuum programs touched**
- **Invariant(s) preserved**
- **Canonical repos/components used**
- **Existing / WIRE**, **Existing / EXTEND**, **NEW / BUILD**, or **DEFER**
- **Allow path**
- **Hostile deny/falsifier path**
- **Consequence sink/readback**
- **Evidence/PGL closure**
- **Proof classification after the change**
- **Known boundary that remains**

A PR that changes consequence behavior without these fields is incomplete.

## Runtime gaps are implementation work

Example: if CAPPO's internal `execute_consequence()` already accepts substrate, boot, runtime-key, state-root or authority-epoch evidence but the public route does not carry those fields, the correct task is to wire the public contract into the existing enforcement. It is not a reason to create a new gate.

## Release candidates

RC1 currently has `accepted=false` in the manifest.

No agent may:

- use RC1 acceptance as a prerequisite for acknowledging older accepted seals;
- rewrite the continuum to match RC1;
- delete proof-backed capabilities merely because RC1 omits them;
- declare RC1 accepted from source/tests alone.

## Evidence migration

Where a historical seal exists but its canonical Git/PGL artifact link is unresolved, preserve the program as accepted with an explicit `evidence linkage pending` boundary and migrate/hash-bind the original artifact. Do **not** regenerate evidence from narrative text.

## Completion

The target state is not a larger document set. The target state is an executable Capability OS whose runtime paths preserve the accepted invariants and whose proof surfaces resolve to the actual evidence estate.
