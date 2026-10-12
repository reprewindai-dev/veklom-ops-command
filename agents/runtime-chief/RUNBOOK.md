# Runbook - runtime-chief

Owned host identity and access path are UNVERIFIED in this repo; observe them first. Never use the retired Hetzner hosts.

## SOP-001: cAPI Health Check
curl https://capi.veklom.com/health
# Expected: {"status":"ok"} HTTP 200

## SOP-002: Verify Service Registration
curl https://capi.veklom.com/api/services
# Expected: JSON array listing all registered backends

## SOP-003: Restart cAPI
# On the owned Docker host (container name LAST_KNOWN):
docker restart capi-container
curl https://capi.veklom.com/health

## SOP-004: Deploy ABIDE Update
# Deploy the reviewed abide-sovereign-control-plane SHA per runbooks/release-deploy.md
curl https://abide.veklom.com/health

## SOP-005: Ollama Verification
curl <OLLAMA_BASE_URL>/api/tags
# OLLAMA_BASE_URL: Ollama on owned/local hardware; address UNVERIFIED
# Expected: JSON with llama3.2:latest in the list
# If Ollama unreachable: ABIDE must return 503 - NOT a fallback blueprint
