# Deployment - governance-chief

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Procedure (deploy and rollback): [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

Host identity, access path, and compose project directory are UNVERIFIED in this repo; observe them on the owned host at deploy time. The retired Hetzner host and `/data/coolify/...` paths must not be used.

## Deploy Gnomledger
Deploy reviewed `gnomledger` SHA per runbooks/release-deploy.md, then:
curl https://pgl.veklom.com/health

## Rollback
Redeploy the previous known-good SHA per runbooks/release-deploy.md and re-verify health.

## Credentials Required (injected by owned-host deployment secret management; mechanism UNVERIFIED)
- DATABASE_URL (gnomledger's own PostgreSQL schema)
- PGL_HMAC_SECRET (for receipt signing)
- CAPI_URL (internal address UNVERIFIED; LAST_KNOWN value in matrices/domain-container-port-map.md)
