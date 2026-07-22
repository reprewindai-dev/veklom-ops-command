#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo 'python3 or python is required' >&2; exit 1; }
export VEKLOM_OPS_ROOT="$ROOT_DIR"
"$PYTHON_BIN" - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ['VEKLOM_OPS_ROOT'])
json_files = []
json_files.extend(sorted((root / 'teams').glob('*/poltergeist.config.json')))
json_files.extend(sorted((root / 'standards').glob('*.json')))
json_files.extend(sorted((root / 'panel' / 'data').glob('*.json')))
json_files.extend(sorted((root / 'reports' / 'toolbox-meetings').glob('*.json')))
json_files.extend(sorted((root / 'reports' / 'department-assignments').glob('*.json')))
json_files.extend(sorted((root / 'reports' / 'agent-runs').glob('*.json')))

jsonl_files = []
for path in [root / 'reports' / 'departments', root / 'reports' / 'command-desk-inbox.jsonl']:
    if path.is_dir():
        jsonl_files.extend(sorted(path.glob('*.jsonl')))
    elif path.exists():
        jsonl_files.append(path)

jsonl_lines = 0

for path in json_files:
    json.loads(path.read_text(encoding='utf-8'))

for path in jsonl_files:
    for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        json.loads(line)
        jsonl_lines += 1

print(f'validated {len(json_files)} JSON files and {len(jsonl_files)} JSONL files ({jsonl_lines} records)')
PY
