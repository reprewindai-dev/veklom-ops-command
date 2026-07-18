#!/usr/bin/env bash
set -euo pipefail

command -v poltergeist >/dev/null 2>&1 || { echo "poltergeist is required" >&2; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PIDS_DIR="${VEKLOM_OPS_PIDS_DIR:-$ROOT_DIR/.runtime/pids}"
mkdir -p "$PIDS_DIR"

CANONICAL_TEAMS=(command-desk poltergeist-platform production-truth release-control build-devex security-secrets runtime-governance evidence-ledger edge-fleet-vnp)
for team in "${CANONICAL_TEAMS[@]}"; do
  config="$ROOT_DIR/teams/$team/poltergeist.config.json"
  team_dir="$(dirname "$config")"
  team="$(basename "$team_dir")"
  pid_file="$PIDS_DIR/$team.pid"
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$team already running (pid $(cat "$pid_file"))"; continue
  fi
  (cd "$team_dir" && poltergeist haunt) >"$team_dir/reports/poltergeist.log" 2>&1 &
  echo $! > "$pid_file"
  echo "started $team"
done
