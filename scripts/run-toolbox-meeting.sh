#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
echo "Toolbox Meeting template: $ROOT_DIR/runbooks/toolbox-meeting.md"
echo 'No production mutation, deployment, SSH, secret rotation, or feature work is authorized by this helper.'
