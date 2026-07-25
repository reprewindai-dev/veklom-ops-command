# Incidents - vnp-chief

## INC-001: Terminal Returns 502
Severity: High | SLA: 15 minutes
1. docker ps --filter name=terminal-veklom
2. docker logs terminal-veklom --tail 50
3. docker restart terminal-veklom
4. curl https://terminal.veklom.com/

## INC-002: Nodes Show Fake Scores
Severity: Critical (Truth Violation) | SLA: Immediate
1. grep -r 'latency.*=.*0\|throughput.*=.*0' veklom-vnp/app/api/routers/nexus.py
2. If found: replace 0 with None (Python) so it serializes as null in JSON
3. Deploy fix and verify null telemetry
4. Report to Production Truth Engineer

## INC-003: Stale Nodes Showing as "Live"
Severity: High | SLA: 30 minutes
1. Check freshness_seconds threshold in status.py
2. Ensure threshold is <= 86400 (24 hours)
3. Remove any methodology override that grants "Connected" status without evidence
