# Incidents - antigravity-chief

## INC-001: Engineer is Stuck or Not Responding
1. Send a message to the engineer subagent
2. If no response after 2 minutes: kill the subagent and respawn with a clearer mission
3. If the task is blocked on a human decision: escalate to founder

## INC-002: Conflicting Ownership Claims
1. Reference contracts/SERVICE_CONTRACTS.md and AGENT_MANIFEST.md
2. If still unclear: escalate to founder for final decision
3. Document the resolution in an ADR

## INC-003: Full Production Outage
1. Notify founder immediately
2. Dispatch platform-chief and runtime-chief simultaneously
3. Monitor progress, coordinate between engineers
4. Ensure only one engineer is modifying each service at a time
