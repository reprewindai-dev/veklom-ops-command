from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import mcp.types as types

from .config import SETTINGS
from .redaction import redact
from .tools import audit, docker, mcp, veklom

TEMPLATE_URI = "ui://veklom/operator-evidence-plane.html"
MIME_TYPE = "text/html+skybridge"
ASSET = Path(__file__).resolve().parent / "assets" / "operator-panel.html"

READ_ONLY = types.ToolAnnotations(
    title="Veklom operator evidence",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _tool_meta() -> dict[str, Any]:
    return {
        "openai/outputTemplate": TEMPLATE_URI,
        "openai/toolInvocation/invoking": "Reading Veklom operational truth",
        "openai/toolInvocation/invoked": "Veklom evidence panel ready",
        "openai/widgetAccessible": False,
        "ui": {"resourceUri": TEMPLATE_URI},
    }


def _resource_meta() -> dict[str, Any]:
    return {
        "openai/widgetPrefersBorder": True,
        "openai/widgetDescription": (
            "Veklom operator evidence plane for runtime truth, security posture, "
            "authority tiers, service health, and MCP audit-chain state."
        ),
    }


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict) and isinstance(value.get("data"), list):
        return len(value["data"])
    return 0


def _failure(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Exception):
        return {"error": type(value).__name__}
    return None


def _compact_health(matrix: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for name, item in matrix.items():
        if not isinstance(item, dict):
            compact[name] = {"state": "UNVERIFIED", "selected": None}
            continue
        selected = item.get("selected") if isinstance(item.get("selected"), dict) else {}
        compact[name] = {
            "state": item.get("state", "UNVERIFIED"),
            "selected": {
                "url": selected.get("url"),
                "status_code": selected.get("status_code"),
                "ok": bool(selected.get("ok")),
            },
        }
    return compact


async def build_snapshot() -> dict[str, Any]:
    containers, health, security = await asyncio.gather(
        docker.list_containers(),
        veklom.health_matrix(),
        veklom.security_posture(),
        return_exceptions=True,
    )

    source_errors = {
        key: failure
        for key, value in {
            "containers": containers,
            "health": health,
            "security": security,
        }.items()
        if (failure := _failure(value)) is not None
    }

    health_value = health if isinstance(health, dict) else {}
    security_value = security if isinstance(security, dict) else {
        "ok": False,
        "proof_state": "UNVERIFIED",
        "error": type(security).__name__ if isinstance(security, Exception) else "Unavailable",
    }

    proof_state = "PARTIAL_RUNTIME_OBSERVATION" if source_errors else "RUNTIME_OBSERVED"
    rows = containers if isinstance(containers, list) else []

    return redact(
        {
            "schema_version": "veklom.operator.snapshot.v2",
            "observed_at": int(time.time()),
            "environment": SETTINGS.environment,
            "proof_state": proof_state,
            "counts": {
                "containers": _count(rows),
                "running": sum(1 for row in rows if row.get("state") == "running"),
                "unhealthy": sum(1 for row in rows if "(unhealthy)" in str(row.get("status", ""))),
                "stopped": sum(1 for row in rows if row.get("state") in {"exited", "created", "dead"}),
            },
            "health": _compact_health(health_value),
            "security": security_value,
            "authority": {
                "writes_enabled": SETTINGS.writes_enabled,
                "database_writes": False,
                "arbitrary_shell": False,
                "secret_value_reads": False,
                "approval_ttl_seconds": SETTINGS.approval_ttl_seconds,
                "credential_classes": ["read", "act"],
                "docker_socket_held_by_mcp": False,
                "approval_audience": SETTINGS.approval_audience,
                "approval_signing_key_present_by_design": False,
            },
            "audit": audit.verify(),
            "source_errors": source_errors,
        },
        max_chars=SETTINGS.max_response_chars,
    )


@mcp.resource(
    TEMPLATE_URI,
    name="Veklom Operator Evidence Plane",
    mime_type=MIME_TYPE,
    meta=_resource_meta(),
)
async def operator_panel_template() -> str:
    return ASSET.read_text(encoding="utf-8")


@mcp.tool(annotations=READ_ONLY)
async def operator_snapshot() -> dict[str, Any]:
    """Return a compact, source-backed Veklom operations snapshot without rendering UI."""
    return await build_snapshot()


@mcp.tool(annotations=READ_ONLY, meta=_tool_meta())
async def render_operator_evidence_plane() -> types.CallToolResult:
    """Render the Veklom operator evidence panel from freshly observed runtime sources."""
    snapshot = await build_snapshot()
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=(
                    "Veklom operator evidence snapshot rendered from current runtime sources. "
                    f"Proof state: {snapshot.get('proof_state', 'UNVERIFIED')}."
                ),
            )
        ],
        structuredContent=snapshot,
        _meta=_tool_meta(),
        isError=False,
    )
