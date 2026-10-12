# Tests - platform-chief

## Network Membership Test (on the owned Docker host)
docker network inspect <network> | jq '.[0].Containers | keys'
# Expected: all production containers that must reach each other are present (network name: UNVERIFIED - read from compose files)

## Port Doctrine Compliance
# Container/port mappings are LAST_KNOWN (matrices/domain-container-port-map.md); re-observe before asserting them.
curl https://capi.veklom.com/health
curl https://pgl.veklom.com/health
curl https://cappo.veklom.com/health
curl https://abide.veklom.com/health
curl https://terminal.veklom.com/

## Ingress Validation (on the owned Docker host)
cloudflared tunnel info <tunnel>
# Expected: active connections, zero routing errors
