# Production Ground Truth

Status: `unverified until live curl evidence is attached`

Current Core V1 runtime authority is owned/local hardware + Docker + Cloudflare Tunnels ([`CURRENT_ARCHITECTURE_LOCK.md`](../CURRENT_ARCHITECTURE_LOCK.md)). Which owned host serves each domain is `UNVERIFIED`. Internal ports are `LAST_KNOWN` from the retired Coolify/Hetzner deployment and must be re-observed.

| Domain | Runtime authority | Internal port (LAST_KNOWN) | Last verified | Evidence |
|---|---|---:|---|---|
| api.veklom.com | UNVERIFIED (owned Docker host) | 8088 | pending | pending |
| control.veklom.com | UNVERIFIED — legacy Control Plane is not a current product surface | 3002 | pending | pending |
| pgl.veklom.com | UNVERIFIED (owned Docker host) | 8001 | pending | pending |
| capi.veklom.com | UNVERIFIED (owned Docker host) | 3003 | pending | pending |
| cappo.veklom.com | UNVERIFIED (owned Docker host) | 8002 | pending | pending |
| abide.veklom.com | UNVERIFIED (owned Docker host) | 3009 | pending | pending |
| gpc.veklom.com | UNVERIFIED (owned Docker host) | 3012 | pending | pending |
| terminal.veklom.com | UNVERIFIED (owned Docker host) | 80 | pending | pending |

This matrix is not a claim of current availability. Update only from a release proof report.
