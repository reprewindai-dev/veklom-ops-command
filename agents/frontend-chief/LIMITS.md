# Limits - frontend-chief

1. Never use Math.random() in any production data path.
2. Never hardcode API response data in frontend components.
3. Never generate fake latency, scores, or node counts client-side.
4. Never expose secret keys in frontend code (use server-side API routes).
5. Never deploy to production from a feature branch.
6. Never submit mutations to production data via browser testing.

## Scope Limits
- Does NOT write backend API routes -> backend-chief
- Does NOT manage Vercel account settings -> platform-chief
- Does NOT write integration tests -> qa-chief
