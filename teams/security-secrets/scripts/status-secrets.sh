#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/check-secrets.sh" >/dev/null && echo 'tracked-content scan passed' || echo 'tracked-content scan failed'
