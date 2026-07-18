#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
grep -q 'Cloudflare Pages' "$ROOT_DIR/runbooks/cloudflare-pages-apex.md"
test -f "$ROOT_DIR/standards/protocol.schema.json"
echo 'runtime boundary contract valid'
