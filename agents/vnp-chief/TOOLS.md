tool_contracts:
  shell:
    allowed:
      - git operations on veklom-vnp, veklom-vnp-standalone
      - python -m pytest tests/
      - curl https://terminal.veklom.com/api/v1/nodes
      - curl https://terminal.veklom.com/api/v1/status
    forbidden:
      - fabricating node metrics
      - hardcoding "Live" status overrides
      - returning 0 for unmeasured latency/throughput

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker logs terminal-veklom --tail 100
      - docker restart terminal-veklom
      - docker ps --filter name=terminal-veklom
    forbidden:
      - modifying other application directories

  github:
    repositories: [veklom-vnp, veklom-vnp-standalone]
    allowed: [read, branch (prefix: vnp/), commit, PR open, merge after sign-off]
    forbidden: [force-push master, skip CI checks]
