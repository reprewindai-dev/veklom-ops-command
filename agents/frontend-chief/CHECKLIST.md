# Definition of Done - frontend-chief

- [ ] Component renders correctly with real backend data
- [ ] Component renders "Unmeasured" or "-" when backend returns null
- [ ] Zero Math.random() calls in production data paths (grep verified)
- [ ] All API calls have error/loading/empty states handled
- [ ] npm run build completes with zero errors
- [ ] Visual check on control.veklom.com confirms changes render correctly
- [ ] Changes committed and pushed
- [ ] Deployed to Vercel (or Coolify) and verified live
- [ ] Production Truth sign-off obtained

## Hard Gates
1. Zero Math.random() in any production metric calculation
2. All null/undefined backend values render as "Unmeasured" or "-"
3. npm run build has zero TypeScript errors
