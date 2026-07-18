#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
grep -q 'stupid-seahorse' "$ROOT_DIR/matrices/server-role-map.md"
grep -q 'veklom-edge-us-east' "$ROOT_DIR/matrices/server-role-map.md"
echo 'fleet role map includes quarantine and edge roles'
