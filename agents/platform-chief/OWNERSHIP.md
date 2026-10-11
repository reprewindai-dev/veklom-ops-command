# Ownership - platform-chief

## Infrastructure Owned
- Ingress routing for owned Docker hosts: Cloudflare Tunnel public-hostname -> service mappings (tunnel names and mappings: UNVERIFIED - observe before acting)
- All docker-compose.yml files across all Veklom applications
- runbooks/release-deploy.md (deployment procedure)

## Canonical Routes
The former Coolify/Traefik route table is retired (history in Git).
Domain -> container -> port mappings are LAST_KNOWN in [matrices/domain-container-port-map.md](../../matrices/domain-container-port-map.md) and must be re-observed.
