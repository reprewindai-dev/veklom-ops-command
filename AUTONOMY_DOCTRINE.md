# Veklom Continuous Operations Doctrine

The operating team is expected to work as a continuous governed loop:

```text
observe → classify → diagnose → authorize → act within scope → verify → record evidence
```

## Risk-tier authority

Every operational capability must resolve to one of four classes before execution:

### LOW — autonomous

Low-risk actions may execute without a human approval when they are explicitly classified and remain inside their declared capability boundary. Typical examples are reads, health checks, topology inspection, evidence verification, redacted logs, and other non-consequential operations.

### MEDIUM — conditional

Medium-risk actions are evaluated against current runtime facts. They may execute autonomously only when the policy can prove the required safety conditions. Examples include reversible lifecycle work such as restart, same-source redeploy, deployment cancellation, bounded scaling, cache invalidation, or proxy reload.

A medium action escalates to approval when, for example:

- production redundancy cannot be proven;
- downtime may occur;
- effective configuration changes;
- an incident is active;
- the source artifact cannot be proven unchanged;
- any required runtime fact is missing or ambiguous.

Missing evidence never becomes permission.

### HIGH — explicit approval

Consequential production/configuration operations require an explicit, scoped approval from the founder or a separately trusted coding-agent authority. Approval must be bound to the exact action and parameters, expire quickly, and be single-use where the execution surface supports it.

### FORBIDDEN — non-bypassable

Some actions are incompatible with the Veklom trust model and must not exist as executable capabilities. Approval cannot override this class.

Examples include:

- database writes/schema destruction through the ops MCP;
- secret-value reads/exports;
- arbitrary host shell;
- disabling fail-closed governance;
- bypassing zero-trust controls;
- removing an air-gap/security boundary to make an operation easier;
- exposing an intentionally private security service merely for convenience;
- destructive volume/prune operations that can erase production state.

## Continuous behavior

- Watch source, runtime, evidence, and declared report/config surfaces.
- Notice failed validation, stale reports, missing handoffs, broken links, unhealthy resources, and drift from doctrine.
- Route each finding to the owning department/capability.
- Diagnose before mutation.
- Classify every proposed operation before execution.
- Execute LOW actions when explicitly authorized by capability policy.
- Execute MEDIUM actions only when current runtime facts satisfy the autonomous guardrails; otherwise escalate.
- Require explicit approval for HIGH actions.
- Deny FORBIDDEN actions regardless of requester or approval state.
- Verify the result against runtime/source truth after any mutation.
- Record evidence for allowed, denied, escalated, failed, and completed operations.
- Never convert uncertainty into a guess or permission.

## No standing production backdoor

Autonomy means authority to perform **bounded capabilities**, not possession of unrestricted production power.

A daemon, model, IDE, ChatGPT connector, coding agent, or other interface receives only the capabilities its credential and policy permit. Production credentials are separated by purpose and must not collapse into a single root credential merely for convenience.

The preferred operational credential pattern is read-first with separately scoped lifecycle/deploy authority. Root access is reserved for exceptional administrative recovery and is not a normal autonomous credential.
