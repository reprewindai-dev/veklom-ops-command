#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
export VEKLOM_OPS_ROOT="$ROOT_DIR"
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo "python3 or python is required" >&2; exit 1; }
"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
import os
json.loads((Path(os.environ['VEKLOM_OPS_ROOT']) / 'standards/release-proof.schema.json').read_text())
print('release proof schema valid')
PY
