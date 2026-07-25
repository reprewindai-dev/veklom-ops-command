# Tests - governance-chief

## Health Test
curl https://pgl.veklom.com/health
# Expected: 200

## Receipt Generation Test
# Execute a governed API call, then check for its receipt
curl https://api.veklom.com/api/v1/compile -X POST -H "Content-Type: application/json" -d '{...}'
curl https://pgl.veklom.com/api/v1/receipts?limit=1
# Expected: receipt with valid HMAC signature

## Mock Receipt Detection Test
curl https://pgl.veklom.com/api/v1/receipts | jq '.[] | select(.type == "mock")'
# Expected: empty array
