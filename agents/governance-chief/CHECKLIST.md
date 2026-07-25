# Definition of Done - governance-chief

- [ ] PGL receipt schema is valid and produces signed receipts
- [ ] Gnomledger settlement flow persists receipts atomically
- [ ] Every governed API execution produces a traceable receipt
- [ ] No mock or synthetic receipts in production
- [ ] curl https://pgl.veklom.com/health -> 200
- [ ] Receipt verification: curl receipt endpoint returns valid HMAC-signed payload
- [ ] Pytest passes with zero failures
- [ ] Changes committed and pushed
- [ ] Platform-chief signaled to redeploy
- [ ] Production Truth sign-off obtained

## Hard Gates
1. PGL health endpoint returns 200
2. No unsettled execution paths (every governed call has a receipt)
3. Zero mock receipts in production ledger
