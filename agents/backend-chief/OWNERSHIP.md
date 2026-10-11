# Ownership - backend-chief

## CAPPO Backend
- Container: cappo-backend-node (LAST_KNOWN) | Port: 8002 (LAST_KNOWN) | Domain: cappo.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Python FastAPI + SQLAlchemy + Alembic
- Critical: cappo_backend/api/routers/, alembic/, docker-compose.yml

## BYOS Backend 2
- Container: UNVERIFIED (former Coolify-generated name removed) | Port: 8088 (LAST_KNOWN) | Domain: api.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Python FastAPI
- Critical: backend/apps/api/routers/benchmarks.py, main.py

## Boundaries (Do NOT Touch)
- gnomledger -> governance-chief
- lockerphycer -> security-chief
- cAPI -> runtime-chief
- Ingress routing (Cloudflare Tunnels) -> platform-chief
