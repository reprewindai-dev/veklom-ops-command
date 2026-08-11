# Domain → Container → Port Map

| Domain | Known runtime mapping | Internal port | Public app port allowed? |
|---|---|---:|---|
| api.veklom.com | n13gp1nhrcdp0hvazvbnlxru-213557155694 | 8088 | no |
| control.veklom.com | veklom-control-plane | 3002 | no |
| pgl.veklom.com | gnomledger-api-1 | 8001 | no |
| capi.veklom.com | capi-container | 3003 | no |
| cappo.veklom.com | cappo-backend-node | 8002 | no |
| abide.veklom.com | abide-node | 3009 | no |
| gpc.veklom.com | gpc-node | 3012 | no |
| terminal.veklom.com | terminal-veklom | 80 | no |
| N/A (internal) | lockerphycer-api | 8092 | no |
| N/A (internal) | veklom-vector-service | 8095 | no |

Expected public exposure: 80/443 and restricted SSH only. Treat mappings as starting truth until verified.
