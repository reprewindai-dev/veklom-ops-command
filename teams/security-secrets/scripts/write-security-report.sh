#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/../reports"
printf '# Security report\n\nGenerated: %s\nNo secret values are written here.\n' "$(date -u +%FT%TZ)" > "$SCRIPT_DIR/../reports/latest.md"
