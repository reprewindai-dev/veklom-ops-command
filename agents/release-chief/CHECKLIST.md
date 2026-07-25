# Definition of Done - release-chief

### Pre-Release
- [ ] All PRs merged to main
- [ ] CI is green on main for all changed repositories
- [ ] qa-chief test certificate obtained
- [ ] security-chief has no outstanding security holds
- [ ] truth-chief sign-off obtained in reports/production-truth-signoffs.jsonl

### Deployment
- [ ] deploy_all.sh executed and exits with code 0
- [ ] docker ps confirms all containers are Up
- [ ] Deployment SHA verified (matches git log on server)

### Post-Release
- [ ] CHANGELOG.md updated
- [ ] Git tag created: vX.Y.Z
- [ ] GitHub release created
- [ ] Live HTTPS curl proof for every changed service
- [ ] Release SHA recorded in reports/releases.jsonl

## Hard Gates
1. CI green on all changed repositories
2. qa-chief test certificate present
3. deploy_all.sh exits with code 0
4. truth-chief sign-off present
