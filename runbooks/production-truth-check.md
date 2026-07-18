# Production Truth Check

Run `scripts/verify-mesh.sh` from a trusted operator machine. Save output as a report with timestamp, commit SHA, and environment. A failed or unreachable endpoint is recorded as failed/unknown, never silently treated as pass.
