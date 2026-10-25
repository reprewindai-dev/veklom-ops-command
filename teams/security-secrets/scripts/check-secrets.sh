#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
tracked="$(git -C "$ROOT_DIR" ls-files)"
if printf '%s\n' "$tracked" | grep -E '(^|/)(\.env|\.env\.[^/]+)$' >/dev/null; then echo 'tracked env file detected' >&2; exit 1; fi
if git -C "$ROOT_DIR" grep -n -I -E '(BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})' -- ':!teams/security-secrets/scripts/check-secrets.sh' >/dev/null; then echo 'credential-like material detected; inspect locally without printing secrets' >&2; exit 1; fi
echo 'no obvious tracked secret material detected'
