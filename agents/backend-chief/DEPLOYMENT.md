# Deployment - backend-chief

## Deploy CAPPO
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/cappo-backend
git stash && git fetch origin && git reset --hard origin/main && git stash pop || true
docker compose up -d --build
"
curl https://cappo.veklom.com/health

## Deploy BYOS
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/veklom-byos-backend
git stash && git fetch origin && git reset --hard origin/main && git stash pop || true
docker compose up -d --build
"
curl https://api.veklom.com/health

## Rollback
git -C /data/coolify/applications/cappo-backend log --oneline -5
git -C /data/coolify/applications/cappo-backend reset --hard <previous-sha>
docker compose -f /data/coolify/applications/cappo-backend/docker-compose.yml up -d --build

## Credentials Required (Coolify-injected)
- DATABASE_URL, REDIS_URL
- CAPI_URL = http://capi-container:3003
- LOCKERPHYCER_URL = http://lockerphycer-api:8092
