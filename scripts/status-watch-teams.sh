#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if command -v poltergeist >/dev/null 2>&1; then
  CANONICAL_TEAMS=(command-desk poltergeist-platform production-truth release-control build-devex security-secrets runtime-governance evidence-ledger edge-fleet-vnp)
  for team in "${CANONICAL_TEAMS[@]}"; do
    config="$ROOT_DIR/teams/$team/poltergeist.config.json"
    team_dir="$(dirname "$config")"
    team="$(basename "$team_dir")"
    echo "=== $team ==="
    (cd "$team_dir" && poltergeist status --verbose) || true
  done
else
  echo "poltergeist not installed; showing configured teams"
  find "$ROOT_DIR/teams" -mindepth 2 -maxdepth 2 -name poltergeist.config.json -print
fi
