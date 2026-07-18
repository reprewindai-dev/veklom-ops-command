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
root = Path(os.environ['VEKLOM_OPS_ROOT'])
for team in teams:
    base = root / 'teams' / team
    for rel in ['team.md','poltergeist.config.json','agents','scripts','reports']:
        assert (base / rel).exists(), f'missing {base/rel}'
    cfg = json.loads((base/'poltergeist.config.json').read_text())
    for key in ['version','projectType','targets','statusScripts','buildScheduling','logging']:
        assert key in cfg, f'{team}: missing {key}'
print(f'validated {len(teams)} teams and Poltergeist configs')
PY
