# Definition of Done - truth-chief

truth-chief's job is to verify that OTHER engineers' Definitions of Done are actually complete.

## Universal Verification Checklist

### For Any Backend Change
- [ ] Live HTTPS curl to changed endpoint returns expected response (not 502, not mock data)
- [ ] Health endpoint returns 200
- [ ] Response schema matches documented contract
- [ ] No synthetic data in the response

### For Any Deployment
- [ ] docker ps on Hetzner confirms container is Up (not Exited, not Restarting)
- [ ] Deployed SHA matches the git commit that was reviewed
- [ ] Live HTTPS response body matches the deployed code's behavior

### For Any Security Fix
- [ ] Unauthenticated request to protected endpoint returns 401
- [ ] Authenticated request returns 200
- [ ] npm audit / pip-audit shows zero high/critical findings

### For Any VNP/Telemetry Change
- [ ] Null fields serialize as null, not 0
- [ ] Stale evidence shows "Insufficient Evidence", not "Live"
- [ ] Node counts reflect only real heartbeat-verified nodes

### Sign-Off Record
- [ ] All above checks completed with live evidence
- [ ] Sign-off written to reports/production-truth-signoffs.jsonl with timestamp and SHA

## Hard Gates - ABSOLUTE
1. Never accept localhost or dev server as production proof
2. Never sign off without running curl against the live public domain
3. Never accept synthetic evidence as real
4. Send work back if any checkbox is not satisfied
