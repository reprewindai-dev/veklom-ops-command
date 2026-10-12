# Runbook - vnp-chief

## SOP-001: Health Check
curl https://terminal.veklom.com/

## SOP-002: Verify Null Telemetry
curl https://terminal.veklom.com/api/v1/nodes | jq '.[0].latency'
# Expected: null (NOT 0)
curl https://terminal.veklom.com/api/v1/nodes | jq '.[0].throughput'
# Expected: null (NOT 0)

## SOP-003: Verify Freshness Enforcement
curl https://terminal.veklom.com/api/v1/status | jq '.capabilities[] | select(.freshness_expired == true)'
# Expected: capabilities with stale evidence show "Insufficient Evidence"

## SOP-004: Deploy VNP Update
# Deploy the reviewed SHA (branch: master) to the owned Docker host per runbooks/release-deploy.md (host UNVERIFIED - observe first)

## SOP-005: Verify No Methodology Overrides
grep -r 'operational_state.*Connected.*status.*Live\|evidence_count.*=.*1' veklom-vnp/app/
# Expected: zero matches
