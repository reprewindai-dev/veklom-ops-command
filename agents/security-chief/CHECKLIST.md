# Definition of Done - security-chief

### Secret Hygiene
- [ ] Zero hardcoded secrets in any source file (grep verified)
- [ ] Zero .env files with real values committed to git
- [ ] All secret references use process.env.SECRET_NAME with no fallback string
- [ ] SEKED_HMAC_SECRET throws error if missing (no fallback)
- [ ] SECRET_KEY in Lockerphycer confirmed >= 64 characters

### Authentication
- [ ] All protected endpoints return 401 for unauthenticated requests
- [ ] All protected endpoints return 403 for unauthorized requests
- [ ] Lockerphycer is the sole auth gateway

### Dependencies
- [ ] npm audit --audit-level=high returns zero high/critical findings
- [ ] pip-audit returns zero high/critical findings
- [ ] All Dependabot alerts acknowledged and tracked

### Proof
- [ ] curl -X GET https://<domain>/protected returns 401
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Zero hardcoded secrets in deployed code
2. Lockerphycer returns 401 for unauthenticated requests
3. All HMAC/JWT secrets sourced from Coolify environment
