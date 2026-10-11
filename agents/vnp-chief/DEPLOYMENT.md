# Deployment - vnp-chief

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Procedure (deploy and rollback): [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

Host identity, access path, and compose project directory are UNVERIFIED in this repo; observe them on the owned host at deploy time. The retired Hetzner host and `/data/coolify/...` paths must not be used.

## Deploy VNP Standalone (Terminal)
Deploy reviewed `vnp-standalone` SHA (branch: master) per runbooks/release-deploy.md, then:
curl https://terminal.veklom.com/

## Rollback
Redeploy the previous known-good SHA per runbooks/release-deploy.md and re-verify.

## Credentials Required (injected by owned-host deployment secret management; mechanism UNVERIFIED)
- DATABASE_URL
- CAPI_URL (internal address UNVERIFIED; LAST_KNOWN value in matrices/domain-container-port-map.md)
