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
files = sorted(root.glob('teams/*/poltergeist.config.json')) + sorted((root/'standards').glob('*.json'))
for path in files:
    json.loads(path.read_text())
print(f'validated {len(files)} JSON files')
PY
