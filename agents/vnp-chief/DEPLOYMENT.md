# Deployment - vnp-chief

## Deploy VNP Standalone (Terminal)
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/vnp-standalone
git stash && git fetch origin && git reset --hard origin/master && git stash pop || true
docker compose up -d --build
"
curl https://terminal.veklom.com/

## Rollback
git -C /data/coolify/applications/vnp-standalone log --oneline -5
git -C /data/coolify/applications/vnp-standalone reset --hard <previous-sha>
docker compose -f /data/coolify/applications/vnp-standalone/docker-compose.yml up -d --build

## Credentials Required (Coolify-injected)
- DATABASE_URL
- CAPI_URL = http://capi-container:3003
