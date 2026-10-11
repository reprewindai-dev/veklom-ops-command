# Ownership - runtime-chief

## cAPI
- Container: capi-container (LAST_KNOWN) | Port: 3003 (LAST_KNOWN) | Domain: capi.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Rust (interlink-rs)

## veklom-vnp-standalone (Terminal)
- Container: terminal-veklom (LAST_KNOWN) | Port: 80 (LAST_KNOWN) | Domain: terminal.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Python FastAPI + Node.js frontend

## abide-sovereign-control-plane (ABIDE)
- Container: abide-node (LAST_KNOWN) | Port: 3009 (LAST_KNOWN) | Domain: abide.veklom.com
- Deploy target: owned Docker host (UNVERIFIED; see runbooks/release-deploy.md)
- Stack: Node.js / TypeScript

## Boundaries (Do NOT Touch)
- cappo-backend -> backend-chief
- veklom-byos-backend-2 -> backend-chief
- gnomledger -> governance-chief
- lockerphycer -> security-chief
- Ingress routing (Cloudflare Tunnels) -> platform-chief
