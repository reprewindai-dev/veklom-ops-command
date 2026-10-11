# Ownership - security-chief

## Lockerphycer
- Container: lockerphycer-api (LAST_KNOWN) | Port: 8092 (LAST_KNOWN; INTERNAL ONLY - no public domain)
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- CRITICAL: SECRET_KEY MUST be >= 64 characters. This is the absolute security backbone.

## RepoGate
- Container: veklom-repo-gate
- Repository: real-repo-gate-for-veklom
- Role: GitHub repository access control

## Cross-Repository Security Ownership
security-chief has audit authority over ALL Veklom repositories:
- .env.example files - must never contain real values
- Auth middleware - must be present in all backends
- Dependency manifests - package.json, requirements.txt, Cargo.toml

## Security Veto
security-chief can halt any deployment from ANY engineer if security risk is identified.
