#!/usr/bin/env bash
set -euo pipefail
PYTHON_BIN="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON_BIN" ]] || { echo 'python3 or python is required' >&2; exit 1; }
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VEKLOM_OPS_ROOT="$ROOT_DIR"
mapfile -t HOSTS < <("$PYTHON_BIN" - <<'PY'
import os
from pathlib import Path

root = Path(os.environ['VEKLOM_OPS_ROOT'])
path = root / 'matrices' / 'domain-container-port-map.md'
for line in path.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line.startswith('|'):
        continue
    parts = [part.strip() for part in line.strip('|').split('|')]
    if not parts or parts[0] in {'Domain', 'Expected public exposure: 80/443 and restricted SSH only. Treat mappings as starting truth until verified.', '---'}:
        continue
    if parts[0].endswith('.com'):
        print(parts[0])
PY
)

if ((${#HOSTS[@]} == 0)); then
  echo 'No hosts could be parsed from matrices/domain-container-port-map.md' >&2
  exit 1
fi

endpoints=(/protocol.json /health /health/dependencies)
failures=0

for host in "${HOSTS[@]}"; do
  echo "=== $host ==="
  for path in "${endpoints[@]}"; do
    if curl --fail --silent --show-error --max-time 15 -o /dev/null -w "$path:%{http_code}\n" "https://$host$path"; then
      :
    else
      echo "$path:unreachable"
      failures=1
    fi
  done

  if curl --fail --silent --show-error --max-time 15 -X POST "https://$host/protocol/introspect" -H 'Content-Type: application/json' -d '{"query":"*"}' -o /dev/null -w '/protocol/introspect:%{http_code}\n'; then
    :
  else
    echo '/protocol/introspect:unreachable'
    failures=1
  fi
done

exit "$failures"
