#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null 2>&1 || { echo 'docker unavailable; no production claim made'; exit 0; }
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo 'Traefik dynamic config inspection is intentionally host-local and read-only.'
if [[ -d /data/coolify/proxy/dynamic ]]; then find /data/coolify/proxy/dynamic -maxdepth 1 -type f -print; fi
