# Definition of Done - platform-chief

### Pre-Deploy
- [ ] docker compose config validates without errors
- [ ] Port numbers match Golden Bible exactly
- [ ] Container name matches Golden Bible exactly
- [ ] Container is in coolify network
- [ ] No exposed ports that should be internal-only

### Deploy
- [ ] docker compose up -d --build exits with code 0
- [ ] docker ps shows container as Up
- [ ] No other containers restarted unexpectedly

### Traefik Routing
- [ ] Dynamic YAML file is syntactically valid
- [ ] Route points to correct container name and port
- [ ] TLS certResolver is set
- [ ] docker logs coolify-proxy shows no routing errors

### Verification
- [ ] curl https://<domain>/health returns 200
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Golden Bible port doctrine enforced - zero deviations
2. All containers in coolify network
3. deploy_all.sh exits with code 0
4. All public domains return 200 on health endpoint
