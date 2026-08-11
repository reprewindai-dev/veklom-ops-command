# Runbook: Coolify Environment Wiring (Vector + MCP)

**Objective**: Hook up the live production environment on Server 2 (Veklom Control Plane) to the internal Vector Service (Server 0) and establish the IDE/MCP Mesh Connection.

## Target Details
- **Application**: `veklom-control-plane`
- **Location**: Coolify Server 2 (US-East Edge)

## Required Environment Variables
Operator must navigate to the Coolify Environment Variable panel for the Control Plane application and inject the following KV pairs:

```env
# Vector Database / Service Integration
VECTOR_SERVICE_URL=http://veklom-vector-service:8095
VECTOR_DB_URL=postgresql://user:pass@llwfyzhnft87bz6brddiax1z:5432/veklom_vectors

# MCP Terminal / IDE Wiring
MCP_MESH_URL=http://capi-container:3003/mcp
```

## Validation Protocol
1. Deploy configuration in Coolify.
2. Confirm that Port 5432 and 8095 are NOT exposed on the public internet, but operate securely across the Hetzner Private Network overlay to Server 0.
3. Test terminal telemetry to ensure the MCP mesh correctly syncs state.
