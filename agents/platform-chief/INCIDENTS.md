# Incidents - platform-chief

Hosts, compose paths, and tunnel names are UNVERIFIED in this repo; observe them on the owned Docker host before acting.

## INC-001: Service Returns 502 (Ingress / Tunnel Failure)
Severity: High | SLA: 10 minutes
1. On the owned host: check cloudflared logs/status for tunnel connection or routing errors
2. Verify the tunnel public-hostname -> service mapping targets the correct container and port
3. docker ps --filter name=<target-container> - is it running?
4. Fix the mapping or restart the service
5. curl https://<domain>/health

## INC-002: Port Conflict on Startup
1. docker ps --format '{{.Names}} {{.Ports}}' - identify conflict
2. Remove explicit host ports: from docker-compose.yml if the tunnel reaches the container over the Docker network
3. Redeploy the service

## INC-003: Container Not Reachable on Docker Network
1. docker inspect <container> | grep Networks
2. If missing from the network the tunnel/peer services use: fix docker-compose.yml networks, redeploy

## INC-004: Deployment Fails Partway
1. Identify failed service from deploy output
2. On the owned host, run docker compose up -d --build for that service per runbooks/release-deploy.md
3. Fix the underlying issue (git conflict or build error)
