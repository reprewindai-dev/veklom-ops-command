# Deployment - security-chief

## Security fixes deployed via platform-chief
security-chief writes the fix, commits and pushes, then signals platform-chief to deploy.

## Secret Rotation Protocol
1. Generate new secret (never reuse old values)
2. Update in Coolify environment variables (UI only)
3. Signal platform-chief to restart affected container
4. Verify: curl -H "Authorization: Bearer <new-token>" https://<domain>/health
5. Document in reports/secret-rotations.jsonl (name and timestamp only)

## Environment Variable Rule
Secrets NEVER leave Coolify. They are never touched locally.
They are never printed in logs. They are never stored in reports.
