# Ownership - security-chief

## Lockerphycer
- Container: lockerphycer-api | Port: 8092 (INTERNAL ONLY - no public domain)
- Server: /data/coolify/applications/lockerphycer/
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
