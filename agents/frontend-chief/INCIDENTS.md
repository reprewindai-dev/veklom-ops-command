# Incidents - frontend-chief

## INC-001: Dashboard Shows Random Numbers Instead of Real Data
Severity: Critical (Truth Violation) | SLA: Immediate
1. grep -r 'Math.random' src/ components/ app/
2. Replace all Math.random() in data paths with null-safe backend reads
3. Deploy fix
4. Verify: empty states show "Unmeasured" or "-"
5. Report to Production Truth Engineer

## INC-002: Frontend Domain is Down
Severity: High | SLA: 15 minutes
1. On the owned Docker host: check the frontend container status and logs (host UNVERIFIED - observe)
2. Check latest git push for build failures: npm run build locally
3. Roll back to the previous known-good SHA per runbooks/release-deploy.md if needed
4. Fix build error, redeploy

## INC-003: API Data Not Loading (Frontend Shows Loading Forever)
Severity: Medium | SLA: 30 minutes
1. Check browser network tab for failed API calls
2. Verify CORS settings on backend
3. Verify the API URL env var is set correctly in the owned host's deployment configuration
4. Check backend health endpoints
