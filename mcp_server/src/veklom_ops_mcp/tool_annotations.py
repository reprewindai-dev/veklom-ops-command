from __future__ import annotations

import mcp.types as types
from mcp.server.fastmcp import FastMCP

READ_ONLY_TOOLS = {
    "operations_policy",
    "evaluate_operation",
    "infrastructure_overview",
    "veklom_health_matrix",
    "security_posture",
    "list_servers",
    "get_server",
    "get_server_resources",
    "get_server_domains",
    "list_applications",
    "get_application",
    "get_application_env_presence",
    "get_application_logs",
    "list_databases",
    "get_database",
    "get_database_backups",
    "list_services",
    "get_service",
    "get_service_logs",
    "list_deployments",
    "get_deployment",
    "verify_mcp_audit_chain",
    "recent_mcp_audit_events",
    "operator_snapshot",
    "render_operator_evidence_plane",
}

MEDIUM_WRITE_TOOLS = {
    "restart_application",
    "restart_service",
    "redeploy_application_same_source",
    "cancel_deployment",
}

HIGH_WRITE_TOOLS = {
    "stop_application",
    "start_stopped_application",
    "stop_service",
    "start_stopped_service",
}


def apply_tool_annotations(mcp: FastMCP) -> None:
    """Attach truthful client hints after every tool has registered.

    The server's policy engine remains authoritative. These annotations only help
    MCP clients present appropriate read/write and confirmation UX.
    """
    manager = mcp._tool_manager  # FastMCP v1.27 implementation detail; SDK is pinned <2.
    registered = {tool.name: tool for tool in manager.list_tools()}
    known = READ_ONLY_TOOLS | MEDIUM_WRITE_TOOLS | HIGH_WRITE_TOOLS
    unexpected = set(registered) - known
    missing = known - set(registered)
    if unexpected or missing:
        details: list[str] = []
        if unexpected:
            details.append("unclassified=" + ",".join(sorted(unexpected)))
        if missing:
            details.append("declared-but-missing=" + ",".join(sorted(missing)))
        raise RuntimeError("MCP authority classification mismatch: " + "; ".join(details))

    for name in READ_ONLY_TOOLS:
        tool = registered[name]
        tool.annotations = types.ToolAnnotations(
            title=tool.title or name.replace("_", " ").title(),
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        )

    for name in MEDIUM_WRITE_TOOLS:
        tool = registered[name]
        tool.annotations = types.ToolAnnotations(
            title=tool.title or name.replace("_", " ").title(),
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        )

    for name in HIGH_WRITE_TOOLS:
        tool = registered[name]
        tool.annotations = types.ToolAnnotations(
            title=tool.title or name.replace("_", " ").title(),
            readOnlyHint=False,
            destructiveHint=name in {"stop_application", "stop_service"},
            idempotentHint=False,
            openWorldHint=False,
        )
