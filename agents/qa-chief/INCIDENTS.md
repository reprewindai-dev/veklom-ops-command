# Incidents - qa-chief

## INC-001: Truth Test Fails in CI
Severity: High - Block the release
1. Identify which endpoint is failing
2. Determine: is it a test bug or a real production failure?
3. If production failure: notify owning engineer, do not merge
4. If test bug: fix the test, re-run, confirm

## INC-002: Test Suite Returns Passing But Production is Broken
Severity: Critical - Tests are lying
1. This means tests are using mocked data
2. Audit all tests: grep -r 'mock\|patch\|MagicMock' tests/
3. Replace mocked endpoints with real production endpoint calls
4. Re-run against live production
