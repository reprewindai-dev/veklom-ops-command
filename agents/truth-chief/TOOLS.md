tool_contracts:
  shell:
    allowed:
      - curl against ALL live production endpoints
      - docker ps on Hetzner (to verify running containers)
      - npm audit --audit-level=high
      - pip-audit
      - openssl dgst -sha256 (to verify file integrity)
      - grep -r 'Math.random|db_seeds|synthetic|mock' <repo>/ (to detect fake data)
    forbidden:
      - accepting localhost or 127.0.0.1 as valid production proof
      - accepting screenshots of local dev servers as proof
      - generating evidence synthetically

  ssh:
    host: root@5.78.135.11 | key: ~/.ssh/veklom-deploy
    allowed:
      - docker ps (container status verification)
      - docker logs <container> --tail 20 (evidence collection)
      - curl from server to verify internal networking
    forbidden:
      - modifying application files
      - modifying deployed code

  browser:
    allowed:
      - visual verification on live production domains
      - capturing screenshots as evidence for frontend changes
    forbidden:
      - submitting mutations to production data
      - accepting local dev server screenshots as proof

  github:
    repositories: all (read-only for evidence review)
    allowed: [read all, review PR diffs, view CI results]
    forbidden: [force-push, merge PRs (that is release-chief's authority)]
