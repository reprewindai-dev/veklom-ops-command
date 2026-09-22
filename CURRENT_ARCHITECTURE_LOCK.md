# CURRENT ARCHITECTURE LOCK

Current Veklom Core V1 infrastructure is owned/local hardware + Docker + Cloudflare Tunnels.

Coolify, Hetzner, Vercel, the legacy Control Plane as current product surface, and any Veklom subsystem named Headless are not part of the current Core V1 architecture.

If any active instruction conflicts with this file or `00_VEKLOM_BIBLE.md`, stop and repair/archive the stale instruction before continuing implementation.


## Capability OS continuum lock — 2026-09-22

The architecture anchor is the accepted Veklom proof-and-seal continuum defined in `continuum/VEKLOM_CONTINUUM_MANIFEST.json`.

- RC1 is **not accepted** and is downstream of this anchor.
- Missing RC1 wiring does not invalidate or downgrade an already accepted scoped seal.
- CAPPO remains the **sole consequence authority**.
- GnomLedger / PGL remains the canonical evidence/provenance/lineage domain.
- V-Chip mechanisms integrate through CAPPO; no second V-Chip consequence gate may be introduced.
- The `vchip-lab/virtualdb-stub` is not the real VirtualDB implementation. The real local VirtualDB source must be exported/hash-bound before coding agents treat VirtualDB as source-integrated.
- Existing proof artifacts are migrated/hash-linked; they are not regenerated from prose.
- Implementation changes must state which continuum invariant/program they preserve or extend and must carry an allow path, a hostile falsifier/deny path, consequence readback, and evidence closure appropriate to the claim.
