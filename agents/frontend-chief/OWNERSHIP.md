# Ownership - frontend-chief

## veklom-control-plane
- Deployment: Vercel | Domain: control.veklom.com
- Stack: Next.js / React / TypeScript
- Critical directories:
  - app/ - Next.js pages and API routes
  - components/ - React components (dashboards, panels, metrics)
  - hooks/ - Data fetching hooks

## veklom-FRONTEND
- Stack: React / Vite / TypeScript
- Critical: components/vnp/BenchmarkPanel.tsx, app/workspace/vnp/page.tsx

## Null Propagation Rule
When backend returns null for any metric field:
- Numeric display: show "-"
- Status display: show "Unmeasured"
- Score display: show "-"
- Never substitute a generated number
