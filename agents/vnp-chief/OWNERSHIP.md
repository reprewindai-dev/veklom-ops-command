# Ownership - vnp-chief

## veklom-vnp (Core VNP)
- Container: terminal-veklom | Port: 80 | Domain: terminal.veklom.com
- Stack: Python FastAPI + Node.js frontend
- Critical files:
  - app/api/routers/status.py (capability assessment, freshness checks)
  - app/api/routers/nexus.py (topology, node registry, null telemetry)
  - app/api/routers/benchmarks.py (scoring algorithms)

## What vnp-chief is responsible for
- Probe ingestion workers
- Nexus topology graph assembly
- Benchmark scoring algorithms
- 24-hour heartbeat freshness enforcement
- Null telemetry propagation (latency, throughput = null when unmeasured)
