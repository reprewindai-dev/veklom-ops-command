tool_contracts:
  shell:
    allowed:
      - git operations on cappo-backend, veklom-byos-backend-2
      - pip install, python -m pytest
      - alembic upgrade head, alembic downgrade -1, alembic revision --autogenerate
      - curl https://cappo.veklom.com/health
      - curl https://api.veklom.com/health
    forbidden:
      - running alembic upgrade on production without QA sign-off
      - deleting database tables directly
      - modifying other engineers' repositories

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker logs cappo-backend-node --tail 100
      - docker logs n13gp1nhrcdp0hvazvbnlxru-213557155694 --tail 100
      - docker restart cappo-backend-node
    forbidden:
      - direct psql access to production database
      - modifying other application directories

  github:
    repositories: [cappo-backend, veklom-byos-backend-2]
    allowed: [read, branch (prefix: backend/), commit, PR open, merge after QA+Truth sign-off]
    forbidden: [force-push main, delete branches, skip CI checks]

  postgresql:
    container: llwfyzhnft87bz6brddiax1z | port: 5432
    allowed: [SELECT queries for debugging, Alembic migrations via app layer]
    forbidden: [direct DROP TABLE or DELETE without migration, other services' schemas]

  redis:
    container: v8vf3lw73fx9lw9xmbq1tvo5 | port: 6379
    allowed: [read cache values for debugging]
    forbidden: [FLUSHDB on production]
