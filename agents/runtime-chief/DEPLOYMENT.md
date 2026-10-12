# Deployment - runtime-chief

## Deployment Authority
runtime-chief deploys: cAPI, ABIDE, VNP Terminal (container names LAST_KNOWN: capi-container, abide-node, terminal-veklom)

Deployment target: owned/local Docker hosts reached via Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Procedure (deploy and rollback): [runbooks/release-deploy.md](../../runbooks/release-deploy.md).

Host identity, access path, and compose project directory are UNVERIFIED in this repo; observe them on the owned host at deploy time. The retired Hetzner host and `/data/coolify/...` paths must not be used.

## Standard Deploy
Deploy the reviewed SHA per runbooks/release-deploy.md.

## Rollback
Redeploy the previous known-good SHA per runbooks/release-deploy.md, then:
curl https://<domain>/health

## Credentials Required (injected by owned-host deployment secret management; mechanism UNVERIFIED)
- SEKED_HMAC_SECRET (min 64 chars, hard error if missing)
- OLLAMA_BASE_URL (Ollama on owned/local hardware; address UNVERIFIED - the former Hetzner address is retired)
- PORT = 3009 (ABIDE), 3003 (cAPI) (LAST_KNOWN)
