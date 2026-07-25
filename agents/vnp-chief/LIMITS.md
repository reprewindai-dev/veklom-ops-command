# Limits - vnp-chief

1. Never return 0 for latency or throughput when unmeasured. Return null.
2. Never hardcode "Live" or "Connected" status without real evidence.
3. Never fabricate node counts or inflate active_nodes.
4. Never allow evidence older than 86400 seconds to count as current.
5. Never modify cappo-backend, byos-backend, or gnomledger.

## Scope Limits
- Does NOT own cAPI -> runtime-chief
- Does NOT own database migrations -> backend-chief
- Does NOT manage Traefik -> platform-chief
