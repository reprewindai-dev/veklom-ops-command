#!/usr/bin/env bash
set -euo pipefail
curl -fsS --max-time 10 https://api.veklom.com/protocol.json >/dev/null && echo 'api protocol reachable' || echo 'api protocol unavailable'
