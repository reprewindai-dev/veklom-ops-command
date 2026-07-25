# Deployment - release-chief

## Full Stack Deploy (Standard)
# From PowerShell on local machine:
$script = Get-Content -Raw C:\Users\antho\.windsurf\deploy_all.sh
ssh -i C:\Users\antho\.ssh\veklom-deploy -o StrictHostKeyChecking=no root@5.78.135.11 $script

## Rollback Protocol
1. Identify last known good release tag: git tag --sort=-creatordate | head -5
2. For each affected repo: git -C /data/coolify/applications/<app-dir> reset --hard <previous-tag>
3. docker compose up -d --build for each affected service
4. Verify all health endpoints return 200
5. Record rollback in reports/releases.jsonl
