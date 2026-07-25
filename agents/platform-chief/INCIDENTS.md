# Incidents - platform-chief

## INC-001: Service Returns 502 (Traefik Failure)
Severity: High | SLA: 10 minutes
1. docker logs coolify-proxy --tail 20 - check routing errors
2. cat /data/coolify/proxy/dynamic/<service>.yaml - verify port
3. docker ps --filter name=<target-container> - is it running?
4. Fix YAML, restart coolify-proxy
5. curl https://<domain>/health

## INC-002: Port Conflict on Startup
1. docker ps --format '{{.Names}} {{.Ports}}' - identify conflict
2. Remove explicit ports: from docker-compose.yml if Traefik handles routing
3. Redeploy the service

## INC-003: Container Not in Coolify Network
1. docker inspect <container> | grep Networks
2. If missing: fix docker-compose.yml to include networks: [coolify], redeploy

## INC-004: deploy_all.sh Fails Partway
1. Identify failed service from script output
2. SSH, navigate to app, run docker compose up -d --build manually
3. Fix the underlying issue (git conflict or build error)
