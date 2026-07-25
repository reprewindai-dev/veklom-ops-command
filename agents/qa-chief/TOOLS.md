tool_contracts:
  shell:
    allowed:
      - pytest tests/ -v (all repositories)
      - curl against all live production endpoints
      - newman (Postman CLI) for API contract tests
      - git operations on test files in any repository
    forbidden:
      - writing tests that use mocked data and claiming they are "truth tests"
      - skipping tests marked as truth-critical
      - marking tests as passing without running them

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - curl from server to test internal networking
      - docker logs <container> to diagnose test failures
    forbidden:
      - modifying production application files

  github:
    repositories: all (test file access)
    allowed: [read all, branch (prefix: qa/), commit test files, open PRs for test additions]
    forbidden: [force-push main, modify source code (write tests only)]
