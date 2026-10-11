# Deployment - security-chief

## Security fixes deployed via platform-chief
security-chief writes the fix, commits and pushes, then signals platform-chief to deploy per [runbooks/release-deploy.md](../../runbooks/release-deploy.md) (owned Docker hosts reached via Cloudflare Tunnels; see [CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)).

## Secret Rotation Protocol
1. Generate new secret (never reuse old values)
2. Update in the owned host's deployment secret management (mechanism UNVERIFIED - observe before acting)
3. Signal platform-chief to restart affected container
4. Verify: curl -H "Authorization: Bearer <new-token>" https://<domain>/health
5. Document in reports/secret-rotations.jsonl (name and timestamp only)

## Environment Variable Rule
Secrets NEVER leave the owned host's deployment secret management. They are never touched locally.
They are never printed in logs. They are never stored in reports.
