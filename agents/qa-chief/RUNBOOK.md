# Runbook - qa-chief

## SOP-001: Full Truth Test Suite
# Run against live production
curl https://capi.veklom.com/health | jq '.status'      # "ok"
curl https://pgl.veklom.com/health | jq '.status'       # healthy
curl https://cappo.veklom.com/health | jq '.status'     # ok
curl https://api.veklom.com/health | jq '.status'       # ok
curl https://abide.veklom.com/health                    # 200
curl https://terminal.veklom.com/                       # 200
curl https://control.veklom.com/                        # 200

## SOP-002: Null Data Test
curl https://api.veklom.com/api/v1/benchmarks/leaderboard | jq '.[] | select(.status == "unmeasured") | .latency'
# Expected: null

## SOP-003: Auth Test
curl -i https://cappo.veklom.com/api/v1/protected | head -1
# Expected: HTTP/2 401

## SOP-004: Run Backend Tests Locally
cd C:\Users\antho\.windsurf\cappo-backend && python -m pytest tests/ -v
cd C:\Users\antho\.windsurf\veklom-byos-backend-2 && python -m pytest tests/ -v
