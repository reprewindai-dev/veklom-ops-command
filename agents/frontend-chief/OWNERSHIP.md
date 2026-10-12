# Ownership - frontend-chief

## veklom-FRONTEND (Capability OS - current product surface)
- Stack: React / Vite / TypeScript
- Deployment: owned Docker host via Cloudflare Tunnels (host and domain UNVERIFIED; see runbooks/release-deploy.md)
- Critical: components/vnp/BenchmarkPanel.tsx, app/workspace/vnp/page.tsx

## veklom-control-plane (retired)
The legacy Control Plane and its Vercel deployment are not the current product surface ([CURRENT_ARCHITECTURE_LOCK.md](../../CURRENT_ARCHITECTURE_LOCK.md)). Do not deploy or extend it; history remains in Git.

## Null Propagation Rule
When backend returns null for any metric field:
- Numeric display: show "-"
- Status display: show "Unmeasured"
- Score display: show "-"
- Never substitute a generated number
