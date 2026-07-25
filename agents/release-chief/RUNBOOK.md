# Runbook - release-chief

## SOP-001: Pre-Release Verification
# Confirm CI is green
gh run list --branch main --limit 5
# Confirm all sign-offs are present
cat reports/production-truth-signoffs.jsonl | tail -5

## SOP-002: Execute Full Deploy
# From PowerShell:
$script = Get-Content -Raw C:\Users\antho\.windsurf\deploy_all.sh
ssh -i C:\Users\antho\.ssh\veklom-deploy -o StrictHostKeyChecking=no root@5.78.135.11 $script

## SOP-003: Verify Deployment SHA
# SSH to Hetzner and check each app's deployed commit:
# git -C /data/coolify/applications/<app> rev-parse HEAD
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
