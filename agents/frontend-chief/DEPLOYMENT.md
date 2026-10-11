# Deployment - frontend-chief

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Procedure (deploy and rollback): [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

The former Vercel deployment of the legacy Control Plane (`veklom-control-plane`) is retired; history remains in Git.

## veklom-FRONTEND (Capability OS)
1. Merge the reviewed change to main (CI green).
2. Deploy per runbooks/release-deploy.md. Host, compose project, and public domain: UNVERIFIED - observe before acting.
3. Verify the live domain returns 200 and renders the change.

## Rollback
Redeploy the previous known-good SHA per runbooks/release-deploy.md
OR: git revert <bad-commit> && git push origin main, then redeploy

## Credentials Required (injected by owned-host deployment secret management; mechanism UNVERIFIED)
- Public API base URLs (e.g. api.veklom.com, capi.veklom.com) - variable names: UNVERIFIED, read from the veklom-FRONTEND repo
- Never expose secret API keys in frontend code (use server-side API routes)
