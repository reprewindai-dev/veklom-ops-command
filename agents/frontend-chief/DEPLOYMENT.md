# Deployment - frontend-chief

## Control Plane (Vercel)
git push origin main
# Vercel deploys automatically from main branch
# Verify: curl https://control.veklom.com -> 200

## Manual Vercel Deploy
cd C:\Users\antho\.windsurf\veklom-control-plane
npx vercel deploy --prod

## Rollback
# In Vercel dashboard: select previous deployment and promote to production
# OR: git revert <bad-commit> && git push origin main

## Credentials Required (Vercel environment variables)
- NEXT_PUBLIC_API_URL = https://api.veklom.com
- NEXT_PUBLIC_CAPI_URL = https://capi.veklom.com
- Never expose secret API keys in frontend code (use server-side API routes)
