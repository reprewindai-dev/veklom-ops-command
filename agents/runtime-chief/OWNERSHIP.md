# Ownership - runtime-chief

## cAPI
- Container: capi-container | Port: 3003 | Domain: capi.veklom.com
- Server: /data/coolify/applications/cAPI/
- Stack: Rust (interlink-rs)

## veklom-vnp-standalone (Terminal)
- Container: terminal-veklom | Port: 80 | Domain: terminal.veklom.com
- Server: /data/coolify/applications/vnp-standalone/
- Stack: Python FastAPI + Node.js frontend

## abide-sovereign-control-plane (ABIDE)
- Container: abide-node | Port: 3009 | Domain: abide.veklom.com
- Server: /data/coolify/applications/abide-sovereign-control-plane/
- Stack: Node.js / TypeScript

## Boundaries (Do NOT Touch)
- cappo-backend -> backend-chief
- veklom-byos-backend-2 -> backend-chief
- gnomledger -> governance-chief
- lockerphycer -> security-chief
- Traefik dynamic configs -> platform-chief
