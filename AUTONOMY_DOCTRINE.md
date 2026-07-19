# Veklom Continuous Operations Doctrine

The department team is expected to operate as a continuous loop:

```text
observe → classify → diagnose → clarify if uncertain → correct if safely authorized → verify → report
```

## Continuous behavior

- Watch the Veklom ops repository and its declared report/config surfaces.
- Notice failed validation, stale reports, missing handoffs, broken links, and drift from doctrine.
- Route each finding to the owning department.
- Ask Chris for clarity when intent, ownership, risk, or desired behavior is ambiguous.
- Correct a problem only when the correction is inside the authorized repo scope, reversible, and supported by proof.
- Pause for approval before production-impacting, security-sensitive, deployment, secret, SSH, or destructive actions.
- Never convert uncertainty into a guess.

The daemon is an orchestrator, not a production backdoor. It has no production tools by default.
