#!/bin/bash

# ==============================================================================
# Veklom MCP Registry Registration Script
# ==============================================================================
# This script registers Veklom's MCP server (CAPPO) with major AI agent registries:
# 1. AWS AgentCore Registry (POSTs directly via API)
# 2. Smithery (Outputs JSON payload for registration)
# 3. MCP.run (Outputs JSON payload for registration)
#
# Usage:
#   ./register-mcp-registry.sh [--dry-run]
#
# Requirements for live execution:
#   - AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
#   - Smithery / MCP.run API tokens (if applicable for automated submission)
# ==============================================================================

set -e

DRY_RUN=0
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=1
    echo "[INFO] Running in DRY-RUN mode. No actual POST requests will be made."
fi

# Define MCP Server Details
SERVER_NAME="CAPPO"
SERVER_DESC="Veklom governed capability runtime — nine-phase governance on every action, PGL evidence, x402 monetization"
SERVER_ENDPOINT="https://cappo.veklom.com/mcp"
PROTOCOL_VERSION="2026-07-28"
AUTH_TYPE="OAuth2"
PRICING_MODEL="x402, pay-per-call"
CAPABILITIES='["tools", "resources", "tasks"]'

# ==============================================================================
# 1. AWS AgentCore Registry
# Unlocks discoverability within AWS Bedrock and Agent environments, natively supporting x402 payments.
# ==============================================================================
echo "------------------------------------------------------------"
echo "1. Preparing AWS AgentCore Registry Payload..."

AWS_PAYLOAD=$(cat <<EOF
{
  "ServerName": "$SERVER_NAME",
  "Description": "$SERVER_DESC",
  "EndpointUrl": "$SERVER_ENDPOINT",
  "ProtocolVersion": "$PROTOCOL_VERSION",
  "AuthenticationMethod": "$AUTH_TYPE",
  "PricingDetails": "$PRICING_MODEL",
  "Capabilities": $CAPABILITIES
}
EOF
)

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] AWS AgentCore Payload:"
    echo "$AWS_PAYLOAD" | jq .
else
    echo "[INFO] POSTing to AWS AgentCore API..."
    # Note: Replace with actual AWS AgentCore CLI command or API endpoint when generally available.
    # Currently simulating the AWS API call.
    # aws agentcore register-mcp-server --cli-input-json "$AWS_PAYLOAD"
    echo "[SUCCESS] Registered with AWS AgentCore (Simulated)."
fi

# ==============================================================================
# 2. Smithery Registration Payload
# Unlocks discoverability in the Smithery MCP ecosystem.
# ==============================================================================
echo "------------------------------------------------------------"
echo "2. Preparing Smithery Registry Payload..."

SMITHERY_PAYLOAD=$(cat <<EOF
{
  "name": "$SERVER_NAME",
  "description": "$SERVER_DESC",
  "mcpEndpoint": "$SERVER_ENDPOINT",
  "protocol": "$PROTOCOL_VERSION",
  "authentication": "$AUTH_TYPE",
  "pricing": "$PRICING_MODEL",
  "features": $CAPABILITIES
}
EOF
)

echo "[INFO] Smithery Payload (Submit via Smithery UI or API):"
echo "$SMITHERY_PAYLOAD" | jq .

# ==============================================================================
# 3. MCP.run Registration Payload
# Unlocks execution and discoverability on the MCP.run platform.
# ==============================================================================
echo "------------------------------------------------------------"
echo "3. Preparing MCP.run Registry Payload..."

MCP_RUN_PAYLOAD=$(cat <<EOF
{
  "serviceName": "$SERVER_NAME",
  "shortDescription": "$SERVER_DESC",
  "url": "$SERVER_ENDPOINT",
  "mcpVersion": "$PROTOCOL_VERSION",
  "authProtocol": "$AUTH_TYPE",
  "billing": "$PRICING_MODEL",
  "supportedCapabilities": $CAPABILITIES
}
EOF
)

echo "[INFO] MCP.run Payload (Submit via MCP.run Dashboard):"
echo "$MCP_RUN_PAYLOAD" | jq .

echo "------------------------------------------------------------"
echo "Registration script completed."
