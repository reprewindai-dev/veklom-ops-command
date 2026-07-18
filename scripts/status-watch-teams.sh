#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if command -v poltergeist >/dev/null 2>&1; then
  for config in "$ROOT_DIR"/teams/*/poltergeist.config.json; do
    team_dir="$(dirname "$config")"
    team="$(basename "$team_dir")"
    echo "=== $team ==="
    (cd "$team_dir" && poltergeist status --verbose) || true
  done
else
  echo "poltergeist not installed; showing configured teams"
  find "$ROOT_DIR/teams" -mindepth 2 -maxdepth 2 -name poltergeist.config.json -print
fi
