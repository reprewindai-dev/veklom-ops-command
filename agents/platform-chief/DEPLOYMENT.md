# Deployment - platform-chief

## Platform-chief owns deployment of ALL services via deploy_all.sh

## Full Stack Deploy
 = Get-Content -Raw C:\Users\antho\.windsurf\deploy_all.sh
ssh -i C:\Users\antho\.ssh\veklom-deploy -o StrictHostKeyChecking=no root@5.78.135.11 

## Individual Service Deploy
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/<app-dir>
git stash && git fetch origin && git reset --hard origin/<branch> && git stash pop || true
docker compose up -d --build
"

## Rollback
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
git -C /data/coolify/applications/<app-dir> log --oneline -5
git -C /data/coolify/applications/<app-dir> reset --hard <previous-sha>
docker compose -f /data/coolify/applications/<app-dir>/docker-compose.yml up -d --build
"
curl https://<domain>/health
