# Incidents - frontend-chief

## INC-001: Dashboard Shows Random Numbers Instead of Real Data
Severity: Critical (Truth Violation) | SLA: Immediate
1. grep -r 'Math.random' src/ components/ app/
2. Replace all Math.random() in data paths with null-safe backend reads
3. Deploy fix
4. Verify: empty states show "Unmeasured" or "-"
5. Report to Production Truth Engineer

## INC-002: control.veklom.com is Down
Severity: High | SLA: 15 minutes
1. Check Vercel dashboard for deployment errors
2. Check latest git push for build failures: npm run build locally
3. Rollback to previous Vercel deployment if needed
4. Fix build error, redeploy

## INC-003: API Data Not Loading (Frontend Shows Loading Forever)
Severity: Medium | SLA: 30 minutes
1. Check browser network tab for failed API calls
2. Verify CORS settings on backend
3. Verify API URL env var is set correctly in Vercel
4. Check backend health endpoints
