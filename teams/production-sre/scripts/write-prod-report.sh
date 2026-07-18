#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/../reports"
printf '# Production SRE report\n\nGenerated: %s\nStatus: inspect live curl output before declaring pass.\n' "$(date -u +%FT%TZ)" > "$SCRIPT_DIR/../reports/latest.md"
