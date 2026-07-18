#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo "python3 or python is required" >&2; exit 1; }
export VEKLOM_OPS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PYTHON_BIN" - <<'PY'
import json
import os
from pathlib import Path
p = Path(os.environ['VEKLOM_OPS_ROOT']) / 'standards/protocol.schema.json'
json.loads(p.read_text())
print(f'protocol schema valid: {p}')
PY
