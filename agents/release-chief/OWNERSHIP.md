# Ownership - release-chief

## Files Owned
- .github/workflows/ in ALL repositories
- deploy_all.sh (master deploy script)
- run_deploys.ps1
- CHANGELOG.md in all repositories
- VERSION files in all repositories
- reports/releases.jsonl (release archive)

## CI Pipeline Requirements
Every repository must have GitHub Actions that:
1. Run on push to main and all PRs
2. Run the full test suite
3. Verify the build succeeds
4. Are required to pass before merge
