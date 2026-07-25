# Definition of Done - backend-chief

- [ ] API endpoint returns correct schema
- [ ] Missing data returns null or "unmeasured" - not a seed value
- [ ] No synthetic seeds in leaderboard or scoring
- [ ] BenchmarkAPISchema fields are Optional where data may be absent
- [ ] Alembic migration created (if schema changed)
- [ ] Migration tested with: alembic upgrade head, then alembic downgrade -1
- [ ] Migration is reversible
- [ ] Unit tests pass locally (pytest)
- [ ] curl https://cappo.veklom.com/health -> 200
- [ ] curl https://api.veklom.com/health -> 200
- [ ] New endpoint has at least one integration test
- [ ] Changes committed and pushed
- [ ] Platform Engineer signaled to redeploy
- [ ] No synthetic or mock data in production response
- [ ] QA Engineer integration tests pass
- [ ] Production Truth sign-off recorded

## Hard Gates
1. Both health endpoints return 200
2. Zero synthetic seed logic in deployed code
3. All Alembic migrations are reversible
