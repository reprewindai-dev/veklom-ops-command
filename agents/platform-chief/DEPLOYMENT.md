# Deployment - platform-chief

## Platform-chief owns deployment of all services to owned Docker hosts

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)).
Procedure (deploy and rollback): [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

## Facts not recorded here (UNVERIFIED)
Host identity, access path, compose project directories, and tunnel names must be observed on the owned host at deploy time.
The retired Hetzner host, `/data/coolify/...` paths, and `deploy_all.sh` must not be used.

## Verify
curl https://<domain>/health
