#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INBOX="$SCRIPT_DIR/../reports/command-desk-inbox.jsonl"
if [[ -f "$INBOX" ]]; then tail -n 20 "$INBOX"; else echo 'Command Desk inbox is empty.'; fi
