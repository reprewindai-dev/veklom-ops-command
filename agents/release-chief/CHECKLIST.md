# Definition of Done - release-chief

### Pre-Release
- [ ] All PRs merged to main
- [ ] CI is green on main for all changed repositories
- [ ] qa-chief test certificate obtained
- [ ] security-chief has no outstanding security holds
- [ ] truth-chief sign-off obtained in reports/production-truth-signoffs.jsonl

### Deployment
- [ ] Deployed per runbooks/release-deploy.md to the observed owned Docker host(s)
- [ ] docker ps confirms all containers are Up
- [ ] Deployment SHA verified on the owned host (matches the reviewed commit)

### Post-Release
- [ ] CHANGELOG.md updated
- [ ] Git tag created: vX.Y.Z
- [ ] GitHub release created
- [ ] Live HTTPS curl proof for every changed service
- [ ] Release SHA recorded in reports/releases.jsonl

## Hard Gates
1. CI green on all changed repositories
2. qa-chief test certificate present
3. Deployment per runbooks/release-deploy.md completed with live HTTPS proof
4. truth-chief sign-off present
