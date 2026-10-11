# Definition of Done - platform-chief

Current Core V1 infrastructure: owned/local hardware + Docker + Cloudflare Tunnels ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)).

### Pre-Deploy
- [ ] docker compose config validates without errors
- [ ] Port numbers match Golden Bible exactly
- [ ] Container name matches Golden Bible exactly
- [ ] Target owned Docker host and compose project observed and recorded (not taken from docs)
- [ ] No exposed ports that should be internal-only

### Deploy
- [ ] docker compose up -d --build exits with code 0
- [ ] docker ps shows container as Up
- [ ] No other containers restarted unexpectedly

### Ingress Routing (Cloudflare Tunnel)
- [ ] Tunnel public-hostname -> service mapping observed and points to the correct container/port
- [ ] cloudflared on the owned host shows no connection/routing errors

### Verification
- [ ] curl https://<domain>/health returns 200
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Golden Bible port doctrine enforced - zero deviations
2. Deployment follows runbooks/release-deploy.md on an owned Docker host
3. All public domains return 200 on health endpoint
