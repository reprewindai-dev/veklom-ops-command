tool_contracts:
  ssh:
    host: root@5.78.135.11
    key: ~/.ssh/veklom-deploy
    allowed:
      - docker logs capi-container --tail 100
      - docker restart capi-container
      - docker restart abide-node
      - docker restart terminal-veklom
      - docker ps --filter name=capi-container
    forbidden:
      - docker rm -f without platform-chief coordination
      - modifying docker-compose.yml on server directly
      - accessing other engineers' application directories

  github:
    repositories: [cAPI, veklom-vnp-standalone, abide-sovereign-control-plane]
    allowed: [read, branch (prefix: runtime/), commit, PR open, merge after sign-off]
    forbidden: [force-push main, delete protected branches, push secrets]

  ollama:
    endpoint: http://167.233.202.195:11434
    allowed_models: [llama3.2:latest, qwen2.5:3b, qwen2.5-coder:1.5b]
    allowed: [POST /api/generate, GET /api/tags]
    forbidden: [using Gemini or any external LLM, exposing endpoint publicly]

  docker:
    scope: owned containers only (capi-container, abide-node, terminal-veklom)
    allowed: [docker logs, docker restart, docker build]
    forbidden: [docker rm -f on other engineers' containers, docker network disconnect]
