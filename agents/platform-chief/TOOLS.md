tool_contracts:
  shell:
    allowed:
      - docker ps
      - docker logs
      - git status
    forbidden:
      - rm -rf /
      - printing secrets
