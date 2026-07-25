tool_contracts:
  shell:
    allowed:
      - git tag, git push --tags
      - gh release create
      - gh pr merge (after all sign-offs)
      - running deploy_all.sh
    forbidden:
      - merging PRs without Production Truth sign-off
      - tagging releases before CI is green
      - deploying without qa-chief test certificate

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - executing deploy_all.sh remotely
      - docker ps (verify containers after deploy)
    forbidden:
      - direct application code changes on server

  github:
    repositories: all
    allowed:
      - merge PRs after: CI green + qa-chief cert + truth-chief sign-off
      - create releases (tags and changelogs)
      - manage branch protection rules
      - write .github/workflows/ files
    forbidden:
      - force-push main or master
      - deleting release tags
      - bypassing branch protection rules
