#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
grep -q 'CURRENT_ARCHITECTURE_LOCK.md' "$ROOT_DIR/matrices/server-role-map.md"
grep -q 'Retired hosts — do not target' "$ROOT_DIR/matrices/server-role-map.md"
echo 'fleet role map defers to the architecture lock and marks retired hosts'
