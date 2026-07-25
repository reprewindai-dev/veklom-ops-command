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
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/vnp-standalone
git stash && git fetch origin && git reset --hard origin/master && git stash pop || true
docker compose up -d --build
"

## SOP-005: Verify No Methodology Overrides
grep -r 'operational_state.*Connected.*status.*Live\|evidence_count.*=.*1' veklom-vnp/app/
# Expected: zero matches
