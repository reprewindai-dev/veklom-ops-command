#!/usr/bin/env bash
# Retired 2026-09-27. This script inspected Coolify/Traefik proxy state, which is
# superseded infrastructure and must not be treated as current. Its versioned
# history remains available in Git. Current Core V1 infrastructure is defined in
# CURRENT_ARCHITECTURE_LOCK.md; observe owned Docker hosts directly per
# runbooks/release-deploy.md.
set -euo pipefail
echo 'scripts/coolify-container-map.sh is retired; see CURRENT_ARCHITECTURE_LOCK.md and runbooks/release-deploy.md' >&2
exit 1
