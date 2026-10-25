#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo "python3 or python is required" >&2; exit 1; }
export VEKLOM_OPS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PYTHON_BIN" - <<'PY'
import json
import os
from pathlib import Path

teams = ['command-desk','poltergeist-platform','production-truth','release-control','build-devex','security-secrets','runtime-governance','evidence-ledger','edge-fleet-vnp']
required_root_files = ['README.md', 'OPS_DOCTRINE.md', 'AUTONOMY_DOCTRINE.md', 'AGENT_HANDOFF_PACKET.md', 'command-router.md', 'VERSION']
required_root_dirs = ['matrices', 'reports', 'runbooks', 'runner', 'scripts', 'standards', 'teams']
required_runbooks = ['toolbox-meeting.md', 'command-desk-inbox.md', 'agent-runner.md', 'mission-response.md']
required_matrices = ['core-backend-4-status.md', 'domain-container-port-map.md', 'production-ground-truth.md', 'protocol-status.md', 'repo-deployment-map.md']
root = Path(os.environ['VEKLOM_OPS_ROOT'])

for rel in required_root_files:
    assert (root / rel).exists(), f'missing {root / rel}'
for rel in required_root_dirs:
    assert (root / rel).exists(), f'missing {root / rel}'
for rel in required_runbooks:
    assert (root / 'runbooks' / rel).exists(), f'missing {root / "runbooks" / rel}'
for rel in required_matrices:
    assert (root / 'matrices' / rel).exists(), f'missing {root / "matrices" / rel}'

for team in teams:
    base = root / 'teams' / team
    for rel in ['team.md','poltergeist.config.json','agents','scripts','reports']:
        assert (base / rel).exists(), f'missing {base / rel}'
    cfg = json.loads((base / 'poltergeist.config.json').read_text(encoding='utf-8'))
    for key in ['version','projectType','targets','statusScripts','buildScheduling','logging']:
        assert key in cfg, f'{team}: missing {key}'

print(f'validated {len(teams)} teams, root docs, matrices, and Poltergeist configs')
PY
bash "$VEKLOM_OPS_ROOT/scripts/validate-json.sh"
