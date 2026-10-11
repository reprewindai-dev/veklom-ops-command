# Edge Fleet Team

Mission: use approved owned edge/probe hosts (inventory UNVERIFIED — see `matrices/server-role-map.md`) as probes, regional runners, staging, and future failover without splitting production state prematurely.

Captain: Edge Fleet Agent

Sub-agents: US-East Probe, EU-Central Probe, EU-North Build Agent, APAC Probe, Failover Planner.

Owned systems: role map, probe plans, private networking assumptions, firewall posture, and regional evidence.

Forbidden: production database deployment, production writes, unapproved failover, or treating unreachable hosts as healthy.

Verification: probe-first checks with explicit server role and timestamp.

Handoff: Security for firewall/network findings; SRE for production impact; Release Manager for approved placement changes.
