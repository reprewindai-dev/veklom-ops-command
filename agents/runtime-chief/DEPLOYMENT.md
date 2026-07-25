# Deployment - runtime-chief

## Deployment Authority
runtime-chief deploys: capi-container, abide-node, terminal-veklom

## Standard Deploy
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/<app-dir>
git stash && git fetch origin && git reset --hard origin/main && git stash pop || true
docker compose up -d --build
"

## Rollback
git -C /data/coolify/applications/<app-dir> log --oneline -10
git -C /data/coolify/applications/<app-dir> reset --hard <good-sha>
docker compose -f /data/coolify/applications/<app-dir>/docker-compose.yml up -d --build
curl https://<domain>/health

## Credentials Required (Coolify-injected only)
- SEKED_HMAC_SECRET (min 64 chars, hard error if missing)
- OLLAMA_BASE_URL = http://167.233.202.195:11434
- PORT = 3009 (ABIDE), 3003 (cAPI)
