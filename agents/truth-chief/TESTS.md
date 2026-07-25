# Tests - truth-chief

truth-chief's tests ARE the production verification suite.

## tests/truth/test_health_all.sh
Runs curl health checks against all live endpoints.
All must return 200.

## tests/truth/test_null_propagation.sh
Verifies unmeasured fields return null, not 0 or fake values.

## tests/truth/test_auth_gates.sh
Verifies protected endpoints return 401 for unauthenticated requests.
Verifies they return 200 for authenticated requests.

## tests/truth/test_sha_verification.sh
Verifies deployed container SHAs match the GitHub main branch HEAD for each repository.

## All tests must run against LIVE PRODUCTION. Never against localhost. Never mocked.
