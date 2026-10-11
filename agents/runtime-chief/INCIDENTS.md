# Incidents - runtime-chief

## INC-001: cAPI Down (502)
Severity: Critical | SLA: 15 minutes
1. docker ps --filter name=capi-container
2. If stopped: docker start capi-container
3. If missing: redeploy cAPI (interlink/interlink-rs) per runbooks/release-deploy.md on the observed owned host
4. Verify: curl https://capi.veklom.com/health

## INC-002: ABIDE Returns 503 (Ollama Unreachable)
Severity: High | SLA: Diagnose within 10 minutes
1. curl <OLLAMA_BASE_URL>/api/tags - is Ollama alive? (owned/local host; address UNVERIFIED)
2. If Ollama down: escalate to platform-chief
3. ABIDE must return 503 - NOT a fake blueprint

## INC-003: Services Not Registering to cAPI
Severity: High | SLA: 20 minutes
1. Verify cAPI is healthy
2. Check: is CAPI_URL = http://capi-container:3003? (never localhost or IP)
3. Restart non-registering service
