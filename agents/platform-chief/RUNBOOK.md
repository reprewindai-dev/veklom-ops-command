# Runbook - platform-chief

Owned host identity and access path are UNVERIFIED in this repo; establish them by fresh observation. Never use the retired Hetzner host.

## SOP-001: Verify All Containers (on the owned Docker host)
docker ps --format 'table {{.Names}}\t{{.Status}}'

## SOP-002: Full Health Check (PowerShell)
@('capi.veklom.com','pgl.veklom.com','cappo.veklom.com','abide.veklom.com','terminal.veklom.com') | ForEach-Object {
  try { $r = Invoke-WebRequest "https://$_/health" -UseBasicParsing -TimeoutSec 10; "$_ -> $($r.StatusCode)" }
  catch { "$_ -> FAILED" }
}

## SOP-003: Fix Ingress Routing (Cloudflare Tunnel)
cloudflared tunnel list
cloudflared tunnel info <tunnel>
# Correct the public-hostname -> service mapping, then re-verify with SOP-002

## SOP-004: Full Deployment
Follow runbooks/release-deploy.md.
