tool_contracts:
  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker ps, docker ps --filter network=coolify
      - docker compose up -d --build
      - docker restart <container>
      - docker logs <container> --tail 100
      - cat /data/coolify/proxy/dynamic/<file>.yaml
      - docker restart coolify-proxy
    forbidden:
      - docker rm -f postgresql or redis containers
      - rm -rf any application directory
      - modifying Coolify internal database

  traefik:
    config_dir: /data/coolify/proxy/dynamic/
    allowed:
      - create new routing YAML files
      - update port numbers and domain rules in existing files
      - docker restart coolify-proxy to apply changes
    forbidden:
      - exposing container names or internal IPs in public routing rules
      - removing TLS certResolver from any route
      - creating routes to non-coolify-network containers

  docker:
    allowed:
      - manage any container lifecycle (start, stop, restart, build)
      - modify docker-compose.yml for any service
    forbidden:
      - destroying volumes containing production data
      - docker system prune without confirming no active sessions

  github:
    repositories: all (deploy scripts and compose files)
    allowed: [read all, commit docker-compose.yml and deploy scripts, open PR for infra changes]
    forbidden: [merge infra PRs without Antigravity review, force-push main]

  environment_variables:
    forbidden: [reading/printing secret values, storing credentials locally, hardcoding in compose files]
    note: All env changes are security-chief domain. Platform-chief confirms presence, not values.
