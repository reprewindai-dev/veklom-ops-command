from __future__ import annotations

import mcp.types as types
from mcp.server.fastmcp import FastMCP

READ_ONLY_TOOLS = {
    "operations_policy",
    "evaluate_operation",
    "infrastructure_overview",
    "health_matrix",
    "security_posture",
    "docker_host_info",
    "list_containers",
    "get_container",
    "get_container_env_presence",
    "get_container_logs",
    "verify_mcp_audit_chain",
    "recent_mcp_audit_events",
    "wait_for_approval",
    "operator_snapshot",
    "render_operator_evidence_plane",
}

MEDIUM_WRITE_TOOLS = {
    "restart_container",
}

HIGH_WRITE_TOOLS = {
    "stop_container",
    "start_stopped_container",
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
            destructiveHint=name == "stop_container",
            idempotentHint=False,
            openWorldHint=False,
        )
