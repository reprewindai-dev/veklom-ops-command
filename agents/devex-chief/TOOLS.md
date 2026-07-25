tool_contracts:
  shell:
    allowed:
      - npm install, npm run build (SDK builds)
      - git operations on veklom-sdk, veklom-amphoteric-sdk
      - documentation generators (typedoc, sphinx, mkdocs)
      - writing README.md in any repository
    forbidden:
      - modifying application source code (write docs and SDKs only)
      - deploying production services

  github:
    repositories: all (documentation access)
    allowed:
      - read all repositories
      - write README.md, CHANGELOG.md, docs/ in any repository
      - commit SDK source code
      - open PRs for documentation changes
    forbidden:
      - force-push main
      - modify source code outside of docs and SDK directories

  browser:
    allowed:
      - verify published documentation renders correctly
      - check API reference pages for accuracy
    forbidden:
      - submitting forms that mutate production data
