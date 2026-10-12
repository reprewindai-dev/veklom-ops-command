# Runbook - frontend-chief

## SOP-001: Audit for Math.random()
grep -r 'Math.random' src/ components/ app/
# Expected: zero matches in data paths (only allowed in crypto ID generation via crypto.randomUUID())

## SOP-002: Build Verification
cd <local veklom-FRONTEND checkout>
npm run build
# Expected: zero errors

## SOP-003: Verify Null State Rendering
# Open browser -> navigate to a panel with no real data
# Verify: numeric cells show "-", status cells show "Unmeasured"
# NOT: random numbers, N/A with generated values

## SOP-004: Deploy
git push origin main
# Deploy per runbooks/release-deploy.md (owned Docker host; host and domain UNVERIFIED - observe)
# Verify: the live frontend domain loads and shows correct data
