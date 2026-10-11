# Domain → Container → Port Map

All mappings below are `LAST_KNOWN` from the retired Coolify/Hetzner deployment. Current Core V1 runtime is owned Docker hosts reached via Cloudflare Tunnels ([`CURRENT_ARCHITECTURE_LOCK.md`](../CURRENT_ARCHITECTURE_LOCK.md)); re-observe before relying on any row.

| Domain | Known runtime mapping | Internal port | Public app port allowed? |
|---|---|---:|---|
| api.veklom.com | UNVERIFIED (former Coolify-generated container name removed) | 8088 | no |
| control.veklom.com | UNVERIFIED — legacy Control Plane (`veklom-control-plane`) is not a current product surface | 3002 | no |
| pgl.veklom.com | gnomledger-api-1 | 8001 | no |
| capi.veklom.com | capi-container | 3003 | no |
| cappo.veklom.com | cappo-backend-node | 8002 | no |
| abide.veklom.com | abide-node | 3009 | no |
| gpc.veklom.com | gpc-node | 3012 | no |
| terminal.veklom.com | terminal-veklom | 80 | no |
| N/A (internal) | lockerphycer-api | 8092 | no |
| N/A (internal) | veklom-vector-service | 8095 | no |

Public exposure of owned hosts: UNVERIFIED. Treat mappings as LAST_KNOWN until verified.
