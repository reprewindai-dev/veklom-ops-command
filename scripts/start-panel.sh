#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
command -v node >/dev/null 2>&1 || { echo 'Node.js 20+ is required' >&2; exit 1; }
cd "$ROOT_DIR/panel"
exec node server.mjs
