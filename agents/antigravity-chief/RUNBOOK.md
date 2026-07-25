# Runbook - antigravity-chief

## SOP-001: Decompose a Mission
1. Read the founder's mission statement
2. Identify which engineers need to be involved
3. Write a task list with explicit owner per item
4. Dispatch engineers (invoke_subagent with scoped mission prompts)
5. Monitor progress, send messages to stuck engineers

## SOP-002: Review a Cross-Cutting PR
1. Read the PR diff
2. Check that the change doesn't violate Golden Bible
3. Check that it doesn't break inter-agent contracts (contracts/SERVICE_CONTRACTS.md)
4. Approve or request changes with specific evidence required

## SOP-003: Write an ADR (Architecture Decision Record)
Location: docs/adr/YYYY-MM-DD-<decision-title>.md
Contents: Context, Decision, Consequences, Alternatives Considered
