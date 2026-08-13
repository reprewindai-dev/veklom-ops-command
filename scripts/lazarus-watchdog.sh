#!/bin/bash
# Lazarus Watchdog Script
# Bounded Fail Operational Semantics for VEKLOM

LOG_FILE="/var/log/lazarus-watchdog.log"

check_and_restart() {
  local service_name=$1
  local url=$2
  local container_name=$3
  
  fails=0
  for i in 1 2 3; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    if [ "$status" != "200" ]; then
      fails=$((fails+1))
      sleep 5
    else
      break
    fi
  done
  
  if [ "$fails" -eq 3 ]; then
    echo "$(date) - [ERROR] $service_name failed 3 consecutive health checks. Restarting container $container_name..." >> "$LOG_FILE"
    docker restart "$container_name" >> "$LOG_FILE" 2>&1
    echo "$(date) - [INFO] Restart command issued for $container_name." >> "$LOG_FILE"
  fi
}

# Run checks
check_and_restart "Cappo Backend" "http://localhost:8002/health" "cappo-backend-node"
check_and_restart "Lockerphycer" "http://localhost:8092/health" "lockerphycer-api"
