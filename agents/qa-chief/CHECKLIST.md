# Definition of Done - qa-chief

For every feature or fix being tested:
- [ ] Integration test covers the success path
- [ ] Integration test covers the null/missing data path (returns null, not a seed)
- [ ] Contract test validates inter-service API schema
- [ ] Failure injection test confirms graceful degradation (not crash)
- [ ] All tests pass with zero failures: pytest -v
- [ ] Truth test suite run against live production
- [ ] Test report generated and attached to PR
- [ ] No SKIP markers on truth-critical tests
- [ ] Production Truth sign-off obtained after passing test suite

## Hard Gates
1. Truth test suite passes against live endpoints (not localhost)
2. Zero failures in integration test suite
3. Every new endpoint has at least one test
