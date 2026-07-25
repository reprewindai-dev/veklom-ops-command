tool_contracts:

  shell:
    description: Local PowerShell / bash execution
    allowed:
      - git add, commit, push
      - gh pr create, gh pr merge
      - docker ps, docker logs
      - curl https://<domain>/health
      - invoke_subagent to spawn engineers
      - read any file
    forbidden:
      - ssh root@5.78.135.11 (escalate to platform-chief or runtime-chief)
      - docker exec into production containers
      - direct database mutations
      - force-push any branch

  github:
    repositories: all
    allowed:
      - read all repositories
      - review and approve PRs from any engineer
      - merge cross-cutting PRs after Production Truth sign-off
      - create ADR documents
      - create GitHub Issues for task tracking
    forbidden:
      - force-push main or master on any repository
      - delete any branch without confirming with owning engineer
      - rewrite commit history
      - bypass branch protection rules

  coolify:
    allowed:
      - view service status in Coolify dashboard
      - read deployment logs
    forbidden:
      - directly trigger Coolify deployments (delegate to platform-chief)
      - modify environment variables in Coolify UI (delegate to security-chief)
      - delete applications in Coolify

  subagent_invocation:
    allowed:
      - invoke any of the Elite 12 engineers as subagents
      - send messages to running subagents
      - kill idle subagents after task completion
    forbidden:
      - invoke more than 5 engineers simultaneously on a single mission
      - invoke engineers without a clearly scoped mission prompt

  files:
    allowed:
      - read any file in any Veklom repository
      - write to veklom-ops-command/ files (doctrine, manifests, ADRs)
      - write Architecture Decision Records
    forbidden:
      - directly edit production source code (delegate to owning engineer)
      - modify .env files

  browser:
    allowed:
      - verify live production domains
      - review GitHub PRs and diffs
      - view Coolify dashboard
    forbidden:
      - submit forms that mutate production state
      - approve Coolify deployments via browser
