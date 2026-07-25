# Ownership - qa-chief

## Test Suites
- cappo-backend/tests/ - CAPPO integration tests
- veklom-byos-backend-2/tests/ - BYOS integration tests
- veklom-vnp/tests/ - VNP integration tests
- gnomledger/tests/ - PGL integration tests
- tests/truth/ (in veklom-ops-command) - Production Truth suite
- tests/contract/ (in veklom-ops-command) - Inter-service contract tests

## CI Requirements
qa-chief writes and maintains GitHub Actions test steps for all repositories.
Every PR must trigger the test suite. No PR merges with a failing test.
