# Deployment - governance-chief

## Deploy Gnomledger
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/gnomledger
git stash && git fetch origin && git reset --hard origin/main && git stash pop || true
docker compose up -d --build
"
curl https://pgl.veklom.com/health

## Rollback
git -C /data/coolify/applications/gnomledger log --oneline -5
git -C /data/coolify/applications/gnomledger reset --hard <previous-sha>
docker compose -f /data/coolify/applications/gnomledger/docker-compose.yml up -d --build

## Credentials Required (Coolify-injected)
- DATABASE_URL (gnomledger's own PostgreSQL schema)
- PGL_HMAC_SECRET (for receipt signing)
- CAPI_URL = http://capi-container:3003
