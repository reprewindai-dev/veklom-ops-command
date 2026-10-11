# Ownership - governance-chief

## Gnomledger (PGL)
- Container: gnomledger-api-1 (LAST_KNOWN) | Port: 8001 (LAST_KNOWN) | Domain: pgl.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Python FastAPI

## What governance-chief is responsible for
- PGL receipt schemas
- Gnomledger settlement and persistence
- Execution identity and traceability
- LAW 0 enforcement across all governed APIs
- Audit replay capability

## Boundaries (Do NOT Touch)
- cappo-backend -> backend-chief
- veklom-byos-backend-2 -> backend-chief
- lockerphycer -> security-chief
