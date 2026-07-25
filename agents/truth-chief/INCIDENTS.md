# Incidents - truth-chief

## INC-001: Engineer Claims Done Without Evidence
Severity: High - Block the release
1. Request specific curl output or screenshot from live production
2. Do not accept "it works on my machine"
3. Do not accept locally-run docker as production proof
4. Send work back until live evidence is provided

## INC-002: Sign-Off Found to Be Based on Synthetic Evidence
Severity: Critical
1. Revoke the sign-off (add revocation entry to signoffs.jsonl)
2. Halt any pending deployment based on that sign-off
3. Re-run verification with real live evidence
4. Identify how synthetic evidence passed through
5. Update verification checklist to prevent recurrence

## INC-003: Production Behavior Contradicts Signed-Off State
Severity: Critical
1. This is a Production Truth failure
2. Document the discrepancy
3. Notify Antigravity
4. Identify which engineer's work caused the discrepancy
5. Require hotfix before any other releases proceed
