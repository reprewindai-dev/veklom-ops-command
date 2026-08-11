# Definition of Done - vnp-chief

- [x] Probe ingestion tested with real node data
- [x] latency and throughput return null when unmeasured (not 0)
- [x] Freshness check: evidence older than 86400 seconds -> "Insufficient Evidence"
- [x] No hardcoded "Live" status overrides
- [x] Node counts reflect only nodes with recent heartbeats
- [x] curl https://terminal.veklom.com/api/v1/nodes returns valid JSON
- [x] curl https://terminal.veklom.com/api/v1/status returns valid JSON
- [x] pytest passes with zero failures
- [x] Changes committed and pushed
- [ ] Platform-chief signaled to redeploy
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Terminal health endpoint returns 200
2. No hardcoded status overrides in deployed code
3. latency and throughput serialize as null when missing
