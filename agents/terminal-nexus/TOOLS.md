tool_contracts:
  shell:
    allowed:
      - docker ps
      - docker logs
    forbidden:
      - rm -rf /
