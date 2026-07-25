# Incidents - backend-chief

## INC-001: CAPPO Returns 502/503
Severity: Critical | SLA: 15 minutes
1. docker ps --filter name=cappo-backend-node
2. docker logs cappo-backend-node --tail 50
3. Look for: database connection errors, migration failures
4. curl https://cappo.veklom.com/health

## INC-002: Leaderboard Returns Fake Scores
Severity: Critical (Truth Violation) | SLA: Immediate
1. grep -r 'db_seeds' backend/ - if found, remove immediately
2. Deploy hotfix
3. Verify leaderboard returns null for unmeasured fields
4. Report to Production Truth Engineer

## INC-003: Migration Failed in Production
Severity: Critical | SLA: 30 minutes
1. STOP further deployments immediately
2. alembic current to determine state
3. alembic downgrade -1 if safe
4. Fix migration, test locally, re-apply
5. Escalate to Antigravity if rollback is impossible
