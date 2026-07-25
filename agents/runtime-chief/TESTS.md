# Tests - runtime-chief

## Health Integration Tests
curl https://capi.veklom.com/health | jq '.status'    # "ok"
curl https://abide.veklom.com/health                   # 200
curl https://terminal.veklom.com/                      # 200

## Service Registration Tests
curl https://capi.veklom.com/api/services | jq '.[].name'
# Expected: includes cappo, byos, gnomledger

## Gemini-Free Tests
grep -r 'generativelanguage.googleapis.com' abide-sovereign-control-plane/
# Expected: zero matches

## Null Telemetry Tests
curl https://terminal.veklom.com/api/v1/nodes | jq '.[0].latency'
# Expected: null (not 0)
