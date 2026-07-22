#!/usr/bin/env bash
set -euo pipefail
FORBIDDEN_PORTS=(3000 3002 5432 6379 8000 8088 8089 8092 8093 8095)
echo 'Expected public exposure: 80/tcp, 443/tcp, restricted SSH only.'
echo "Forbidden public application/data ports: ${FORBIDDEN_PORTS[*]}"

violations=()
checked_any=false

if command -v ss >/dev/null 2>&1; then
  checked_any=true
  while IFS= read -r line; do
    for port in "${FORBIDDEN_PORTS[@]}"; do
      if [[ "$line" =~ :$port([[:space:]]|$) ]]; then
        violations+=("ss: $line")
        break
      fi
    done
  done < <(ss -H -ltn)
fi

if command -v docker >/dev/null 2>&1; then
  checked_any=true
  while IFS=$'\t' read -r name ports; do
    [[ -n "${name:-}" ]] || continue
    for port in "${FORBIDDEN_PORTS[@]}"; do
      if [[ "$ports" == *":$port"* || "$ports" == *"->$port/"* || "$ports" == *"$port/tcp"* ]]; then
        violations+=("docker: $name :: $ports")
        break
      fi
    done
  done < <(docker ps --format '{{.Names}}\t{{.Ports}}')
fi

if [[ "$checked_any" != true ]]; then
  echo 'Unable to verify public ports: ss and docker are both unavailable.' >&2
  exit 2
fi

if ((${#violations[@]})); then
  echo 'Forbidden public ports detected:' >&2
  printf ' - %s\n' "${violations[@]}" >&2
  exit 1
fi

echo 'No forbidden public application/data ports are exposed in the checks available on this host.'
