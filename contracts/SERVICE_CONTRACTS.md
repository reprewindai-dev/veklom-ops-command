# Inter-Agent Service Contracts
# Veklom Ops Command

These contracts define how services communicate with each other. Every engineer must
honor these contracts when building or modifying their owned services. If a contract
needs to change, the owning engineer of both sides must coordinate.

---

## CONTRACT: CAPPO -> cAPI (Registration)

**Owner A:** backend-chief (CAPPO)
**Owner B:** runtime-chief (cAPI)
**Direction:** CAPPO -> cAPI on boot

### API Contract
- **Endpoint:** POST http://capi-container:3003/register
- **Method:** POST
- **Timing:** On application startup (within 10 seconds)
- **Request Schema:**
  {
    "service_name": "cappo",
    "service_url": "http://cappo-backend-node:8002",
    "health_endpoint": "/health",
    "version": "<semver>"
  }
- **Expected Response:** HTTP 200 {"registered": true}
- **Failure Mode:** If cAPI is unreachable, CAPPO logs a warning and retries every 30 seconds. It does not crash.

### SLA
- cAPI must be running before CAPPO registers. platform-chief ensures startup order.
- Registration must succeed within 60 seconds of CAPPO boot.

### Escalation: runtime-chief owns the /register endpoint. backend-chief owns the registration call.

---

## CONTRACT: BYOS -> cAPI (Registration)

**Owner A:** backend-chief (BYOS)
**Owner B:** runtime-chief (cAPI)

### API Contract
- **Endpoint:** POST http://capi-container:3003/register
- **Same schema as CAPPO registration above**
- service_name: "byos", service_url: "http://n13gp1nhrcdp0hvazvbnlxru-213557155694:8088"

---

## CONTRACT: BYOS -> Gnomledger (Receipt Submission)

**Owner A:** backend-chief (BYOS)
**Owner B:** governance-chief (Gnomledger)
**Direction:** BYOS -> Gnomledger after every governed API compile

### API Contract
- **Endpoint:** POST http://gnomledger-api-1:8001/api/v1/receipts
- **Method:** POST
- **Request Schema:**
  {
    "execution_id": "<uuid>",
    "service": "byos",
    "operation": "compile",
    "timestamp": "<ISO8601>",
    "caller_identity": "<identity>",
    "hmac_signature": "<sha256-hmac>"
  }
- **Expected Response:** HTTP 201 {"receipt_id": "<uuid>", "persisted": true}
- **Failure Mode:** If Gnomledger is unreachable, BYOS queues the receipt and retries. It does not skip the receipt.
- **Version Compatibility:** API v1 - stable

### SLA
- Gnomledger must respond within 2 seconds for receipt submission
- Receipts must be persisted within 5 seconds of submission

---

## CONTRACT: CAPPO -> Lockerphycer (Auth Verification)

**Owner A:** backend-chief (CAPPO)
**Owner B:** security-chief (Lockerphycer)
**Direction:** CAPPO -> Lockerphycer for every protected request

### API Contract
- **Endpoint:** POST http://lockerphycer-api:8092/verify
- **Request Schema:**
  {
    "token": "<jwt-bearer-token>",
    "required_scope": "<scope-string>"
  }
- **Expected Response (valid token):** HTTP 200 {"valid": true, "identity": {...}}
- **Expected Response (invalid token):** HTTP 401 {"valid": false, "reason": "..."}
- **Failure Mode:** If Lockerphycer is unreachable, CAPPO returns HTTP 503 - it never fails open.
- **Timeout:** 1 second maximum. If Lockerphycer does not respond in 1s, return 503.

---

## CONTRACT: VNP -> BYOS (Benchmark Data)

**Owner A:** vnp-chief (VNP/Terminal)
**Owner B:** backend-chief (BYOS)
**Direction:** BYOS pulls benchmark data from VNP for leaderboard

### API Contract
- **Endpoint:** GET http://terminal-veklom:80/api/v1/benchmarks
- **Expected Response:**
  [
    {
      "node_id": "<uuid>",
      "latency_p50": null or <float>,
      "latency_p95": null or <float>,
      "throughput": null or <float>,
      "measured_at": "<ISO8601> or null",
      "status": "measured" or "unmeasured"
    }
  ]
- **Null Contract:** latency and throughput MUST be null when unmeasured. BYOS must NOT substitute 0 or a default.
- **Freshness:** Data older than 86400 seconds must be marked "unmeasured", not used as current

---

## CONTRACT: Frontend -> All Backends (API Calls)

**Owner:** frontend-chief
**Direction:** Frontend -> Public HTTPS endpoints

### Null Propagation Contract
The frontend MUST honor this contract for ALL backend null responses:
- If backend returns null for a numeric field: display "-"
- If backend returns null for a status field: display "Unmeasured"
- If backend returns null for a score: display "-"
- NEVER substitute a generated number for a backend null

### Health Endpoint Contract
All backends expose: GET /health
Expected: HTTP 200 {"status": "ok"} or {"healthy": true}

---

## CONTRACT: truth-chief -> All Engineers (Sign-Off Protocol)

**Direction:** truth-chief -> release-chief (via signoffs.jsonl)

### Sign-Off Format
Every entry in reports/production-truth-signoffs.jsonl must contain:
{
  "timestamp": "<ISO8601>",
  "release_sha": "<git-commit-sha>",
  "services_verified": ["cappo", "byos", "pgl", ...],
  "evidence": [
    { "service": "cappo", "url": "https://cappo.veklom.com/health", "status": 200, "body_excerpt": "..." },
    ...
  ],
  "signed_by": "truth-chief",
  "verdict": "APPROVED" or "REJECTED",
  "rejection_reason": "<if REJECTED, why>"
}

### Escalation
release-chief must check for a APPROVED sign-off before executing deploy_all.sh.
If the latest sign-off is REJECTED, halt the release immediately.
