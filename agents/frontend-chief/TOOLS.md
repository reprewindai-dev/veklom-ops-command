tool_contracts:
  shell:
    allowed:
      - npm install, npm run dev, npm run build
      - git operations on veklom-control-plane, veklom-FRONTEND
      - npx vercel deploy --prod (after Production Truth sign-off)
      - grep -r 'Math.random' src/ (to audit for fake data)
    forbidden:
      - Math.random() in any production data path
      - hardcoding API response data
      - generating fake latency or scores client-side

  github:
    repositories: [veklom-control-plane, veklom-FRONTEND]
    allowed: [read, branch (prefix: frontend/), commit, PR open, merge after sign-off]
    forbidden: [force-push main, hardcode secret API keys in frontend code]

  browser:
    allowed:
      - verify live UI on control.veklom.com
      - test that "Unmeasured" and "-" render correctly when backend returns null
      - visual regression testing
    forbidden:
      - submitting forms that mutate production data
      - approving Coolify deployments via browser

  vercel:
    allowed: [deploy from main branch after Production Truth sign-off]
    forbidden: [deploy from feature branches to production]
