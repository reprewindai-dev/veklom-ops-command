# Runbook - security-chief

## SOP-001: Secret Audit
grep -r 'SEKED_SYSTEM_COVENANT_SECRET|password123|default_secret' C:\Users\antho\.windsurf\
# Expected: zero matches

## SOP-002: Dependency Audit
cd <repo> && npm audit --audit-level=high
pip-audit -r requirements.txt

## SOP-003: Verify SECRET_KEY Length (Without Printing Value)
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
docker exec lockerphycer-api sh -c 'echo -n \"\\" | wc -c'
"
# Expected: 64 or more

## SOP-004: Verify Auth is Active
# Unauthenticated -> 401
curl -i https://cappo.veklom.com/api/v1/protected-endpoint
# Authenticated -> 200
curl -i -H "Authorization: Bearer <valid-token>" https://cappo.veklom.com/api/v1/protected-endpoint

## SOP-005: Rotate Secret (Protocol)
1. Generate new secret (minimum 64 characters for SECRET_KEY)
2. Update in Coolify environment variables (UI only - never locally)
3. Signal platform-chief to restart the affected container
4. Verify auth still works
5. Document in reports/secret-rotations.jsonl (name only, never value)
