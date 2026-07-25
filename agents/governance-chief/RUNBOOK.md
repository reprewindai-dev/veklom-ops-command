# Runbook - governance-chief

## SOP-001: PGL Health Check
curl https://pgl.veklom.com/health
# Expected: HTTP 200

## SOP-002: Verify Receipts Being Generated
curl https://pgl.veklom.com/api/v1/receipts?limit=5
# Expected: JSON array of recent receipts with HMAC signatures

## SOP-003: Verify Receipt Cryptographic Integrity
curl https://pgl.veklom.com/api/v1/receipts/<receipt-id>/verify
# Expected: {"valid": true, "signed": true}

## SOP-004: Deploy Gnomledger
ssh -i ~/.ssh/veklom-deploy root@5.78.135.11 "
cd /data/coolify/applications/gnomledger
git stash && git fetch origin && git reset --hard origin/main && git stash pop || true
docker compose up -d --build
"
curl https://pgl.veklom.com/health
