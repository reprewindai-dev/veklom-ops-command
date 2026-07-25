# Runbook - platform-chief

## SOP-001: Verify All Containers
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "docker ps --format 'table {{.Names}}\t{{.Status}}'"

## SOP-002: Full Health Check (PowerShell)
@('capi.veklom.com','pgl.veklom.com','cappo.veklom.com','abide.veklom.com','terminal.veklom.com') | ForEach-Object {
  try {  = Invoke-WebRequest "https://" -UseBasicParsing -TimeoutSec 10; " -> " }
  catch { " -> FAILED" }
}

## SOP-003: Fix Traefik Routing
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11
# Edit /data/coolify/proxy/dynamic/<service>.yaml with correct port
docker restart coolify-proxy
docker logs coolify-proxy 2>&1 | tail -20  # Verify no routing errors

## SOP-004: Full Deployment
 = Get-Content -Raw C:\Users\antho\.windsurf\deploy_all.sh
ssh -i C:\Users\antho\.ssh\veklom-deploy root@5.78.135.11 
