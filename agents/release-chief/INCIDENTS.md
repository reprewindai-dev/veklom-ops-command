# Incidents - release-chief

## INC-001: deploy_all.sh Fails
Severity: High | SLA: 30 minutes
1. Identify failed service from output
2. SSH, navigate to app, diagnose
3. Fix (git conflict or build error) and retry failed service
4. Full health check when all services are up

## INC-002: Production SHA Mismatch
Severity: Critical
1. ssh: git -C /data/coolify/applications/<app-dir> rev-parse HEAD
2. Compare with GitHub main branch HEAD
3. If mismatch: git reset --hard origin/main && docker compose up -d --build
4. Re-verify health endpoints

## INC-003: CI Failing on Main
Severity: High - Main is not deployable
1. Identify failing test
2. Notify owning engineer - do not deploy until CI is green
