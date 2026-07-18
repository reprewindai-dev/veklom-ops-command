#!/usr/bin/env bash
set -euo pipefail
curl -fsS --max-time 10 https://api.veklom.com/health >/dev/null && echo 'api health reachable' || echo 'api health unavailable'
