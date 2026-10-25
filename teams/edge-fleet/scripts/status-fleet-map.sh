#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
awk -F'|' 'NF >= 4 && $2 !~ /Server/ && $2 !~ /---/ {print $2 " -> " $3}' "$ROOT_DIR/matrices/server-role-map.md"
