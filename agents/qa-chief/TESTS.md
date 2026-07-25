# Tests - qa-chief

qa-chief IS the test authority. The test suites qa-chief writes are the source of truth.

## Truth Test Categories
1. Health tests - every service health endpoint returns 200
2. Null propagation tests - unmeasured fields return null, not 0 or fake values
3. Auth tests - protected endpoints return 401 without credentials
4. Schema tests - API responses match declared schemas
5. Contract tests - inter-service calls return expected structures
6. Freshness tests - stale VNP data shows "Insufficient Evidence"

## CI Integration
Every GitHub Actions workflow must include:
  - name: Run Truth Tests
    run: pytest tests/truth/ -v --tb=short
  Pass-required: true
