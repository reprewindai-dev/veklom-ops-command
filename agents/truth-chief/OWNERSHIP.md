# Ownership - truth-chief

## Primary Ownership
- reports/production-truth-signoffs.jsonl - sign-off archive
- tests/truth/ - Production Truth verification suite
- The sign-off process itself

## What truth-chief builds
truth-chief builds the verification suite - the automated and manual checks that
confirm production is in the state it is claimed to be.

## Verification Suite Location
veklom-ops-command/tests/truth/
- test_health_all.sh - health endpoint checks for all services
- test_null_propagation.sh - verify null telemetry
- test_auth_gates.sh - verify 401/403 on protected endpoints
- test_sha_verification.sh - verify deployed SHAs match GitHub
