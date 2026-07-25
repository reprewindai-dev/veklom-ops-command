# Definition of Done - vnp-chief

- [ ] Probe ingestion tested with real node data
- [ ] latency and throughput return null when unmeasured (not 0)
- [ ] Freshness check: evidence older than 86400 seconds -> "Insufficient Evidence"
- [ ] No hardcoded "Live" status overrides
- [ ] Node counts reflect only nodes with recent heartbeats
- [ ] curl https://terminal.veklom.com/api/v1/nodes returns valid JSON
- [ ] curl https://terminal.veklom.com/api/v1/status returns valid JSON
- [ ] pytest passes with zero failures
- [ ] Changes committed and pushed
- [ ] Platform-chief signaled to redeploy
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Terminal health endpoint returns 200
2. No hardcoded status overrides in deployed code
3. latency and throughput serialize as null when missing
