#!/usr/bin/env bash
set -euo pipefail
HOSTS=(api.veklom.com bingo.veklom.com governance.veklom.com control.veklom.com interlink.veklom.com pgl.veklom.com duel.veklom.com capi.veklom.com cappo.veklom.com vnp.veklom.com lockerphycer.veklom.com)
for host in "${HOSTS[@]}"; do
  echo "=== $host ==="
  for path in /protocol.json /health /health/dependencies; do
    curl --fail --silent --show-error --max-time 15 -o /dev/null -w "$path:%{http_code}\n" "https://$host$path" || echo "$path:unreachable"
  done
  curl --fail --silent --show-error --max-time 15 -X POST "https://$host/protocol/introspect" -H 'Content-Type: application/json' -d '{"query":"*"}' -o /dev/null -w '/protocol/introspect:%{http_code}\n' || echo '/protocol/introspect:unreachable'
done
