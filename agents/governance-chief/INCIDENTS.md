# Incidents - governance-chief

## INC-001: PGL Down (502)
Severity: High | SLA: 15 minutes
1. docker ps --filter name=gnomledger-api-1
2. docker logs gnomledger-api-1 --tail 50
3. Restart: docker restart gnomledger-api-1
4. Verify: curl https://pgl.veklom.com/health

## INC-002: Mock Receipt Found in Production Ledger
Severity: Critical (Truth Violation) | SLA: Immediate
1. Identify the source that generated the mock receipt
2. Mark the receipt as INVALID in the ledger
3. Fix the source code to stop generating mock receipts
4. Deploy fix, verify real receipts are generated
5. Report to Production Truth Engineer

## INC-003: Receipt HMAC Signature Invalid
Severity: High | SLA: 30 minutes
1. Check PGL_HMAC_SECRET is set and correct
2. Verify the signing algorithm matches verification algorithm
3. Fix signing code or key reference
4. Redeploy and re-test
