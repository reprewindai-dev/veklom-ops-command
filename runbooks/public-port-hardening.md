# Public Port Hardening

Public exposure is restricted to 80/443 and tightly controlled SSH. Application and data ports `3000, 3002, 8000, 8088, 8089, 5432, 6379` must remain private. Run `scripts/check-public-ports.sh` on the host and attach evidence.
