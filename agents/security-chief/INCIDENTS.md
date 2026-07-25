# Incidents - security-chief

## INC-001: Hardcoded Secret Found in Source
Severity: CRITICAL | SLA: Immediate - STOP ALL DEPLOYMENTS
1. Halt all deployments
2. Identify the secret and which commits it appears in
3. Remove from source code immediately
4. Rotate the compromised secret in Coolify
5. Force-push is ONLY permitted for removing committed secrets
6. Notify Antigravity immediately
7. Document in security incident log

## INC-002: Lockerphycer Down
Severity: Critical | SLA: 15 minutes
1. docker ps --filter name=lockerphycer-api
2. Restart: docker restart lockerphycer-api
3. Verify SECRET_KEY length (SOP-003)
4. If key < 64 chars: rotate via Coolify UI, restart
5. Verify: auth endpoints return 401 for unauthenticated requests

## INC-003: Dependency Vulnerability
Severity: High (7 days) / Critical (24h)
1. npm audit --audit-level=high OR pip-audit
2. Identify affected package
3. Update to patched version
4. Test existing functionality
5. Commit and deploy
