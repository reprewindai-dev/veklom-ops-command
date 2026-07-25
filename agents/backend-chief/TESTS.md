# Tests - backend-chief

## Owned Test Suites
- cappo-backend/tests/ - CAPPO integration tests
- veklom-byos-backend-2/tests/ - BYOS integration tests

## Required Per Endpoint
1. Success case with valid data
2. Missing data case - verify null returned (NOT a seed value)
3. Schema validation test

## Truth Tests
curl https://api.veklom.com/api/v1/benchmarks/leaderboard | jq '.[] | select(.status == "unmeasured")'
# All unmeasured entries must have null numeric fields

## CI Requirements
- pytest tests/ -v must pass with zero failures
- No SKIP markers on truth-critical tests
