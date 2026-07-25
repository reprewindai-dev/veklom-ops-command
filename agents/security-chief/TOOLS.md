tool_contracts:
  shell:
    allowed:
      - grep -r 'SEKED_SYSTEM_COVENANT|hardcoded_secret|password123' <repo>/
      - npm audit --audit-level=high
      - pip-audit
      - echo -n "" | wc -c (verify key length without printing value)
    forbidden:
      - printing or logging any secret value
      - storing credentials in any file in this repository
      - hardcoding credentials in source files

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker logs lockerphycer-api --tail 100
      - docker ps --filter name=lockerphycer
      - docker inspect lockerphycer-api (to check env var NAMES, NOT values)
    forbidden:
      - printing environment variable values
      - modifying other containers' environment variables
      - reading /data/coolify database files

  github:
    repositories: all (audit access)
    allowed:
      - read all repositories for security audit
      - commit security fixes to any repository
      - view and resolve Dependabot alerts
    forbidden:
      - force-push any main branch (exception: removing committed secrets)
      - committing .env files with real values
      - bypassing branch protection

  coolify:
    allowed: [view environment variable NAMES to confirm presence]
    forbidden: [viewing or printing secret values, sharing Coolify login credentials]
