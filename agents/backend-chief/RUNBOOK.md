# Runbook - backend-chief

## SOP-001: Health Check
curl https://cappo.veklom.com/health
curl https://api.veklom.com/health

## SOP-002: Run Tests
cd C:\Users\antho\.windsurf\cappo-backend && python -m pytest tests/ -v
cd C:\Users\antho\.windsurf\veklom-byos-backend-2 && python -m pytest tests/ -v

## SOP-003: Create Migration
alembic revision --autogenerate -m "describe_change"
# Review the generated migration file
alembic upgrade head
alembic current

## SOP-004: Verify No Synthetic Seeds
grep -r 'db_seeds' veklom-byos-backend-2/backend/
# Expected: zero matches

## SOP-005: Container Logs
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "docker logs cappo-backend-node --tail 50"
