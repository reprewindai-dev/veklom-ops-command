# Ownership - backend-chief

## CAPPO Backend
- Container: cappo-backend-node | Port: 8002 | Domain: cappo.veklom.com
- Server: /data/coolify/applications/cappo-backend/
- Stack: Python FastAPI + SQLAlchemy + Alembic
- Critical: cappo_backend/api/routers/, alembic/, docker-compose.yml

## BYOS Backend 2
- Container: n13gp1nhrcdp0hvazvbnlxru-213557155694 | Port: 8088 | Domain: api.veklom.com
- Server: /data/coolify/applications/veklom-byos-backend/
- Stack: Python FastAPI
- Critical: backend/apps/api/routers/benchmarks.py, main.py

## Boundaries (Do NOT Touch)
- gnomledger -> governance-chief
- lockerphycer -> security-chief
- cAPI -> runtime-chief
- Traefik routing -> platform-chief
