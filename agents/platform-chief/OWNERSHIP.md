# Ownership - platform-chief

## Infrastructure Files
- /data/coolify/proxy/dynamic/*.yaml - ALL Traefik routing configs
- deploy_all.sh - master deployment script
- All docker-compose.yml files across all Veklom applications

## Canonical Traefik Routes
| File | Routes To |
|---|---|
| capi.yaml | capi-container:3003 |
| abide.yaml | abide-node:3009 |
| cappo.yaml | cappo-backend-node:8002 |
| pgl.yaml | gnomledger-api-1:8001 |
| veklom.yaml | n13gp1nhrcdp0hvazvbnlxru-213557155694:8088 |
| terminal.yaml | terminal-veklom:80 |

## Network: coolify Docker network - all production containers must be members
