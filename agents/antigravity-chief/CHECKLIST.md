# Definition of Done — antigravity-chief

Nothing is marked complete until every applicable checkbox is checked.

## Mission-Level Checklist

### Decomposition
- [ ] Mission received from founder
- [ ] Mission broken into domain-specific tasks
- [ ] Each task assigned to a named engineer (e.g., `platform-chief`, `backend-chief`)
- [ ] Task boundaries are non-overlapping
- [ ] Ambiguities identified and clarified before engineers are dispatched

### Execution
- [ ] All assigned engineers have reported back
- [ ] Each engineer's output includes evidence (build log, curl response, test output)
- [ ] No engineer reported a silent failure
- [ ] Production Truth Engineer has signed off

### Deployment
- [ ] Release Engineer has run `deploy_all.sh` (or equivalent scoped deploy)
- [ ] Deployment SHA recorded in `reports/`
- [ ] Live HTTPS verification completed for every changed service

### Documentation
- [ ] ADR written if architecture changed
- [ ] `AGENT_MANIFEST.md` updated if team structure changed
- [ ] Founder briefed on outcome

### Evidence
- [ ] No synthetic or locally-generated evidence accepted as proof
- [ ] All curl probes run against live public domains (not localhost)
- [ ] Evidence timestamped and archived in `reports/`

## Hard Gates
These are binary. The mission does NOT close until all are true:
1. Production Truth Engineer sign-off exists in `reports/production-truth-signoffs.jsonl`
2. Deployment SHA matches what is running in production (`docker ps` confirms)
3. Public HTTPS curl returns expected response body
