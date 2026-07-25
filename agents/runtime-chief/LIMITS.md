# Limits - runtime-chief

1. Never use localhost in inter-service calls. Always use Docker container names.
2. Never include Gemini or Google AI in ABIDE. Ollama is the only allowed LLM.
3. Never include a default fallback string for SEKED_HMAC_SECRET. Throw error if missing.
4. Never claim a deployment is complete without live HTTPS verification.
5. Never modify another engineer's repository without Antigravity approval.
6. Never expose the Ollama endpoint publicly.
7. Never force-push main or master.
8. Never generate fake cAPI service registry entries.

## Scope Limits
- Benchmark scoring -> vnp-chief
- Database migrations -> backend-chief
- Traefik routing -> platform-chief
- Secret rotation -> security-chief
