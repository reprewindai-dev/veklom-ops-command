# Runbook - release-chief

## SOP-001: Pre-Release Verification
# Confirm CI is green
gh run list --branch main --limit 5
# Confirm all sign-offs are present
cat reports/production-truth-signoffs.jsonl | tail -5

## SOP-002: Execute Full Deploy
# Follow runbooks/release-deploy.md for each changed service.
# Owned host identity and access path: UNVERIFIED - observe; never use the retired Hetzner host or deploy_all.sh.

## SOP-003: Verify Deployment SHA
# On the owned Docker host, read the SHA each running service was built from (docker inspect / compose project checkout)
# Compare with: gh api repos/reprewindai-dev/<repo>/branches/main | jq '.commit.sha'

## SOP-004: Tag Release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
gh release create v1.2.3 --title "Release v1.2.3" --notes-file CHANGELOG.md

## SOP-005: Post-Deploy Health Check
foreach ($domain in @('capi.veklom.com','pgl.veklom.com','cappo.veklom.com','abide.veklom.com','terminal.veklom.com')) {
  try { $r = Invoke-WebRequest "https://$domain/health" -UseBasicParsing -TimeoutSec 10; "$domain -> $($r.StatusCode)" }
  catch { "$domain -> FAILED" }
}
