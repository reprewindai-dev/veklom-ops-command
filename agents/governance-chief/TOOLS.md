tool_contracts:
  shell:
    allowed:
      - git operations on gnomledger
      - python -m pytest tests/
      - curl https://pgl.veklom.com/health
      - curl https://pgl.veklom.com/api/v1/receipts
    forbidden:
      - creating mock or synthetic receipts in production
      - modifying the ledger directly without proper governance flows

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker logs gnomledger-api-1 --tail 100
      - docker restart gnomledger-api-1
      - docker ps --filter name=gnomledger
    forbidden:
      - direct database mutations to the ledger table
      - modifying other application directories

  github:
    repositories: [gnomledger]
    allowed: [read, branch (prefix: governance/), commit, PR open, merge after sign-off]
    forbidden: [force-push main, skip CI checks]

  postgresql:
    container: llwfyzhnft87bz6brddiax1z | port: 5432
    allowed: [SELECT queries on gnomledger tables for audit]
    forbidden: [INSERT/UPDATE/DELETE directly on ledger tables, modifying other services' schemas]
