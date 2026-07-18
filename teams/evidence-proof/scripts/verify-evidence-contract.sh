#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export VEKLOM_OPS_ROOT="$ROOT_DIR"
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo "python3 or python is required" >&2; exit 1; }
"$PYTHON_BIN" - <<'PY'
import json
import os
from pathlib import Path
for p in ['standards/agent-report.schema.json','standards/release-proof.schema.json']:
    json.loads((Path(os.environ['VEKLOM_OPS_ROOT']) / p).read_text())
print('evidence contracts valid')
PY
