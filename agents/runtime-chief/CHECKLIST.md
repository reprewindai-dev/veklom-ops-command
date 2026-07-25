# Definition of Done - runtime-chief

- [ ] Code builds locally without errors
- [ ] No localhost in any inter-service networking call
- [ ] ABIDE uses Ollama exclusively - zero Gemini code paths
- [ ] SEKED_HMAC_SECRET throws hard error if missing (no fallback string)
- [ ] curl https://capi.veklom.com/health -> 200 {"status":"ok"}
- [ ] curl https://abide.veklom.com/health -> 200
- [ ] curl https://terminal.veklom.com/ -> 200
- [ ] Changes committed and pushed to GitHub
- [ ] Container confirmed running: docker ps --filter name=capi-container
- [ ] Live HTTPS proof captured
- [ ] Production Truth Engineer has signed off
- [ ] Sign-off recorded in reports/production-truth-signoffs.jsonl

## Hard Gates
1. cAPI health endpoint returns 200
2. All registered backends appear in cAPI service registry
3. Zero localhost in deployed code
