# Deployment - antigravity-chief

antigravity-chief coordinates deployments but does not execute them directly.
Deployments flow through: antigravity-chief -> release-chief -> platform-chief

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Procedure: [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

## Exception: Emergency
If release-chief and platform-chief are both unavailable, antigravity-chief may execute runbooks/release-deploy.md directly on the observed owned Docker host.
Host identity and access path: UNVERIFIED — establish by fresh observation; never use the retired Hetzner host or deploy_all.sh.
This is an emergency-only action.
