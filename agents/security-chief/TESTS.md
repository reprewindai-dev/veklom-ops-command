# Tests - security-chief

## Auth Tests
curl -i https://cappo.veklom.com/api/v1/users | head -1
# Expected: HTTP/2 401

curl -i -H "Authorization: Bearer " https://cappo.veklom.com/api/v1/users | head -1
# Expected: HTTP/2 200

## Secret Hygiene Tests
grep -rn 'SEKED_SYSTEM_COVENANT_SECRET|default_hmac|hardcoded_key' C:\Users\antho\.windsurf\
# Expected: zero results

## Dependency Audit Tests
npm audit --audit-level=high 2>&1 | grep 'found 0 vulnerabilities'
# Expected: found 0 vulnerabilities
