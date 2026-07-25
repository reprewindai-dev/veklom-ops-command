# Runbook - runtime-chief

## SOP-001: cAPI Health Check
curl https://capi.veklom.com/health
# Expected: {"status":"ok"} HTTP 200

## SOP-002: Verify Service Registration
curl https://capi.veklom.com/api/services
# Expected: JSON array listing all registered backends

## SOP-003: Restart cAPI
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "docker restart capi-container"
curl https://capi.veklom.com/health

## SOP-004: Deploy ABIDE Update
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/abide-sovereign-control-plane &&
git pull origin main &&
docker build -t abide-node:latest . &&
docker rm -f abide-node &&
docker run -d --name abide-node --network coolify -p 3009:3009 abide-node:latest
"
curl https://abide.veklom.com/health

## SOP-005: Ollama Verification
curl http://167.233.202.195:11434/api/tags
# Expected: JSON with llama3.2:latest in the list
# If Ollama unreachable: ABIDE must return 503 - NOT a fallback blueprint
