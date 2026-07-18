#!/usr/bin/env bash
set -euo pipefail
echo 'Expected public exposure: 80/tcp, 443/tcp, restricted SSH only.'
echo 'Forbidden public application/data ports: 3000 3002 8000 8088 8089 5432 6379.'
if command -v ss >/dev/null 2>&1; then ss -tulpn; fi
if command -v docker >/dev/null 2>&1; then docker ps --format 'table {{.Names}}\t{{.Ports}}'; fi
