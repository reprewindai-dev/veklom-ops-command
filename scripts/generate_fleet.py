import os
import json
import re

ROOT_DIR = r"C:\Users\antho\.windsurf\veklom-ops-command"
AGENTS_DIR = os.path.join(ROOT_DIR, "agents")
RUNNER_FILE = os.path.join(ROOT_DIR, "runner", "runner.mjs")

FLEET = {
    "backend-chief": "Primary backend orchestration.",
    "security-chief": "System-wide security and secret rotation.",
    "platform-chief": "Infrastructure and port allocations.",
    "runtime-chief": "Nervous system and registry (cAPI).",
    "qa-chief": "Quality assurance and testing.",
    "release-chief": "Deployment scheduling and CI/CD.",
    "frontend-chief": "Frontend builds and CDN caches.",
    "devex-chief": "Developer experience and tooling.",
    "protocol-mesh-captain": "Traefik routing and network mesh.",
    "abide-governance-engineer": "ABIDE Sovereign Control Plane enforcement.",
    "terminal-nexus-commander": "VNP Terminal Edge Telemetry.",
    "codebase-architect": "Deep codebase inspection and repository reading.",
    "abide-truth-auditor": "Audits ABIDE ledger for cryptographic integrity.",
    "cappo-truth-auditor": "Audits CAPPO for financial ledger integrity.",
    "byos-truth-auditor": "Audits BYOS for backend truth and invariants.",
    "vnp-truth-auditor": "Audits VNP for telemetry truth.",
    "frontend-truth-auditor": "Audits frontend UI state against truth constraints.",
    "abide-execution-ops": "Deploys and maintains ABIDE containers.",
    "byos-execution-ops": "Deploys and maintains BYOS containers.",
    "vnp-execution-ops": "Deploys and maintains VNP standalone containers.",
    "cappo-execution-ops": "Deploys and maintains CAPPO containers.",
    "frontend-execution-ops": "Deploys and maintains frontend and control-plane edge nodes.",
    "cappo-service-restorer": "Responds to and restores CAPPO service outages.",
    "byos-service-restorer": "Responds to and restores BYOS API outages.",
    "gnomledger-service-restorer": "Responds to and restores PGL outages.",
    "abide-deployment-monitor": "Actively monitors ABIDE deployment health."
}

def create_agent(name, role):
    path = os.path.join(AGENTS_DIR, name)
    os.makedirs(path, exist_ok=True)
    
    agent_md = f"""# Agent: {name} | Role: {role}

## Mission
You are the {name}. Your domain is {role}. 
You must strictly enforce the Golden Bible rules and ensure production stability.

## Escalation Chain
Diagnose issue -> Create local patch -> Test locally -> Escalate to Antigravity for deployment.

## Success Metrics
- Zero unapproved infrastructure mutations.
- Fast, autonomous root cause analysis within your domain.
"""
    tools_md = """tool_contracts:
  shell:
    allowed:
      - docker ps
      - docker logs
      - git status
    forbidden:
      - rm -rf /
      - printing secrets
"""
    with open(os.path.join(path, "AGENT.md"), "w") as f:
        f.write(agent_md)
    with open(os.path.join(path, "TOOLS.md"), "w") as f:
        f.write(tools_md)
    
    print(f"Generated {name}")

def update_runner():
    with open(RUNNER_FILE, "r") as f:
        content = f.read()
    
    teams_array_str = "const TEAMS = [\n" + ",\n".join([f"  '{k}'" for k in FLEET.keys()]) + "\n];"
    
    # Replace the TEAMS array block
    content = re.sub(r'const TEAMS = \[.*?\];', teams_array_str, content, flags=re.DOTALL)
    
    with open(RUNNER_FILE, "w") as f:
        f.write(content)
    print("Updated runner.mjs with 26-agent TEAMS array.")

if __name__ == "__main__":
    for name, role in FLEET.items():
        create_agent(name, role)
    update_runner()
    print("Fleet generation complete.")
