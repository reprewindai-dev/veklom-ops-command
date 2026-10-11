# Deployment - release-chief

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)).

## Full Stack Deploy (Standard)
Follow [runbooks/release-deploy.md](../../runbooks/release-deploy.md) for each changed service.
Host identity, access path, and compose project directories are UNVERIFIED in this repo; observe them on the owned host and record them in the release proof.
The retired `deploy_all.sh` over SSH to the Hetzner host must not be used.

## Rollback Protocol
1. Identify last known good release tag: git tag --sort=-creatordate | head -5
2. For each affected service: redeploy that tag on its owned Docker host per runbooks/release-deploy.md
3. Verify all health endpoints return 200
4. Record rollback in reports/releases.jsonl
