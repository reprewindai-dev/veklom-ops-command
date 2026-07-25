# Runbook - truth-chief

## SOP-001: Full Production Truth Sweep
# Run against live production - never localhost

echo "=== HEALTH CHECKS ==="
foreach ( in @('https://capi.veklom.com/health','https://pgl.veklom.com/health','https://cappo.veklom.com/health','https://api.veklom.com/health','https://abide.veklom.com/health','https://terminal.veklom.com/')) {
  try {  = Invoke-WebRequest  -UseBasicParsing -TimeoutSec 10; "[PASS]  -> " }
  catch { "[FAIL] " }
}

echo "=== NULL TELEMETRY CHECK ==="
curl https://terminal.veklom.com/api/v1/nodes | jq '.[0] | {latency, throughput}'
# Both must be null

echo "=== AUTH GATE CHECK ==="
curl -i https://cappo.veklom.com/api/v1/users | head -1
# Must be 401

echo "=== SHA VERIFICATION ==="
# Manually compare docker rev-parse HEAD vs GitHub branch HEAD for each service

## SOP-002: Reject Work
If any check fails, send work back to owning engineer:
- Document which check failed
- Document what was found vs what was expected
- Do NOT sign off until all checks pass

## SOP-003: Issue Sign-Off
When all checks pass, write to reports/production-truth-signoffs.jsonl:
{ "timestamp": "<ISO8601>", "release": "<version or SHA>", "signed_by": "truth-chief", "evidence": [...] }
