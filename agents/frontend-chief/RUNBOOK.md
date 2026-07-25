# Runbook - frontend-chief

## SOP-001: Audit for Math.random()
grep -r 'Math.random' src/ components/ app/
# Expected: zero matches in data paths (only allowed in crypto ID generation via crypto.randomUUID())

## SOP-002: Build Verification
cd C:\Users\antho\.windsurf\veklom-control-plane
npm run build
# Expected: zero errors

## SOP-003: Verify Null State Rendering
# Open browser -> navigate to a panel with no real data
# Verify: numeric cells show "-", status cells show "Unmeasured"
# NOT: random numbers, N/A with generated values

## SOP-004: Deploy to Vercel
cd C:\Users\antho\.windsurf\veklom-control-plane
git push origin main
# Vercel auto-deploys from main
# Verify: https://control.veklom.com loads and shows correct data
