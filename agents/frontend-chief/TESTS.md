# Tests - frontend-chief

## Math.random() Audit Test
grep -r 'Math.random' src/ components/ app/
# Expected: zero results in any data computation path

## Null State Rendering Test
# In unit tests: render component with null backend response
# Verify: renders "Unmeasured" or "-" instead of throwing or showing 0

## Build Test
npm run build
# Expected: zero TypeScript errors, zero build failures

## Visual Verification
# Navigate to control.veklom.com
# Find a panel with no real data
# Verify: "Unmeasured" shown, not a generated number
