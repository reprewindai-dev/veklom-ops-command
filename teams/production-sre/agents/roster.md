# Production SRE Agent Roster

Router Auditor traces domain → proxy → service → port. Container Doctor reads state without mutation. Health Verifier executes HTTPS health/protocol probes. Incident Scribe records timelines. Port Exposure Auditor compares host exposure with policy.

Every agent returns status, observed_at, scope, checks, evidence_refs, blocking_findings, and handoff.
