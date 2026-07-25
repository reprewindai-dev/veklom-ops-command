# Tests - vnp-chief

## Null Telemetry Tests
curl https://terminal.veklom.com/api/v1/nodes | jq '.[0].latency'
# Expected: null

curl https://terminal.veklom.com/api/v1/nodes | jq '.[0].throughput'
# Expected: null

## Freshness Tests
# Evidence older than 86400s must not claim "Live"
grep -r 'freshness_seconds > 86400' veklom-vnp/app/api/routers/status.py
# Expected: at least one match (the enforcement check)

## No Methodology Override Test
grep -r 'evidence_count = 1' veklom-vnp/app/api/routers/status.py
# Expected: zero matches
