# Tests - platform-chief

## Network Membership Test
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "docker network inspect coolify | jq '.[0].Containers | keys'"
# Expected: all production container IDs present

## Port Doctrine Compliance
curl https://capi.veklom.com/health    # -> capi-container:3003
curl https://pgl.veklom.com/health     # -> gnomledger-api-1:8001
curl https://cappo.veklom.com/health   # -> cappo-backend-node:8002
curl https://abide.veklom.com/health   # -> abide-node:3009
curl https://terminal.veklom.com/      # -> terminal-veklom:80

## Traefik Validation
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "docker logs coolify-proxy 2>&1 | grep -i error"
# Expected: zero routing errors
