# Incidents - release-chief

## INC-001: Deployment Fails
Severity: High | SLA: 30 minutes
1. Identify failed service from output
2. On the owned Docker host (observed, not assumed), diagnose
3. Fix (git conflict or build error) and retry failed service per runbooks/release-deploy.md
4. Full health check when all services are up

## INC-002: Production SHA Mismatch
Severity: Critical
1. On the owned Docker host: read the SHA the running container was built from (docker inspect / compose project checkout)
2. Compare with GitHub main branch HEAD
3. If mismatch: redeploy the reviewed SHA per runbooks/release-deploy.md
4. Re-verify health endpoints

## INC-003: CI Failing on Main
Severity: High - Main is not deployable
1. Identify failing test
2. Notify owning engineer - do not deploy until CI is green
