#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PIDS_DIR="${VEKLOM_OPS_PIDS_DIR:-$ROOT_DIR/.runtime/pids}"
shopt -s nullglob
for pid_file in "$PIDS_DIR"/*.pid; do
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then kill "$pid"; echo "stopped $(basename "$pid_file" .pid)"; fi
  rm -f "$pid_file"
done
