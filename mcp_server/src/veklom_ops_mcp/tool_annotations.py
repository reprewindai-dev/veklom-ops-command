from __future__ import annotations

import mcp.types as types
from mcp.server.fastmcp import FastMCP

READ_ONLY_TOOLS = {
    "operations_policy",
    "evaluate_operation",
    "infrastructure_overview",
    "veklom_health_matrix",
    "security_posture",
    "list_applications",
    "get_application",
    "get_application_logs",
    "list_databases",
    "get_database",
    "get_database_backups",
    "list_services",
    "get_service",
    "list_deployments",
    "get_deployment",
    "verify_mcp_audit_chain",
    "recent_mcp_audit_events",
    "operator_snapshot",
    "render_operator_evidence_plane",
}

MEDIUM_WRITE_TOOLS = {
    "restart_application",
    "redeploy_application_same_source",
    "cancel_deployment",
}

HIGH_WRITE_TOOLS = {
    "stop_application",
    "start_stopped_application",
}


def apply_tool_annotations(mcp: FastMCP) -> None:
    """Attach truthful client hints after every tool has registered.

    The server's policy engine remains authoritative. These annotations only help
    MCP clients present appropriate read/write and confirmation UX.
    """
    manager = mcp._tool_manager  # FastMCP v1.27 public implementation detail; SDK is pinned <2.
    registered = {tool.name: tool for tool in manager.list_tools()}
    known = READ_ONLY_TOOLS | MEDIUM_WRITE_TOOLS | HIGH_WRITE_TOOLS
    unexpected = set(registered) - known
    if unexpected:
        raise RuntimeError(
            "MCP tool(s) lack an explicit authority/annotation class: " + ", ".join(sorted(unexpected))
        )

    for name in READ_ONLY_TOOLS:
        tool = registered.get(name)
        if tool:
            tool.annotations = types.ToolAnnotations(
                title=tool.title or name.replace("_", " ").title(),
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=False,
            )

    for name in MEDIUM_WRITE_TOOLS:
        tool = registered.get(name)
        if tool:
            tool.annotations = types.ToolAnnotations(
                title=tool.title or name.replace("_", " ").title(),
                readOnlyHint=False,
                destructiveHint=False,
                idempotentHint=False,
                openWorldHint=False,
            )

    for name in HIGH_WRITE_TOOLS:
        tool = registered.get(name)
        if tool:
            tool.annotations = types.ToolAnnotations(
                title=tool.title or name.replace("_", " ").title(),
                readOnlyHint=False,
                destructiveHint=name == "stop_application",
                idempotentHint=False,
                openWorldHint=False,
            )
