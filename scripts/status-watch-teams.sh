#!/usr/bin/env bash
set -euo pipefail
if command -v poltergeist >/dev/null 2>&1; then
  poltergeist status --verbose || true
else
  echo "poltergeist not installed; showing configured teams"
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  find "$SCRIPT_DIR/../teams" -mindepth 2 -maxdepth 2 -name poltergeist.config.json -print
fi
