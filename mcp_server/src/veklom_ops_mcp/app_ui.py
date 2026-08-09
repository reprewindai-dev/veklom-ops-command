from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import mcp.types as types

from .config import SETTINGS
from .redaction import redact
from .tools import audit, coolify, mcp, veklom

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
    applications, databases, services, deployments, health, security = await asyncio.gather(
        coolify.list_applications(),
        coolify.list_databases(),
        coolify.list_services(),
        coolify.list_deployments(),
        veklom.health_matrix(),
        veklom.security_posture(),
        return_exceptions=True,
    )

    source_errors = {
        key: failure
        for key, value in {
            "applications": applications,
            "databases": databases,
            "services": services,
            "deployments": deployments,
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

    if source_errors:
        proof_state = "PARTIAL_RUNTIME_OBSERVATION"
    else:
        proof_state = "RUNTIME_OBSERVED"

    return redact(
        {
            "schema_version": "veklom.operator.snapshot.v1",
            "observed_at": int(time.time()),
            "environment": SETTINGS.environment,
            "proof_state": proof_state,
            "counts": {
                "applications": _count(applications),
                "databases": _count(databases),
                "services": _count(services),
                "deployments": _count(deployments),
            },
            "health": _compact_health(health_value),
            "security": security_value,
            "authority": {
                "writes_enabled": SETTINGS.writes_enabled,
                "database_writes": False,
                "arbitrary_shell": False,
                "secret_value_reads": False,
                "approval_ttl_seconds": SETTINGS.approval_ttl_seconds,
                "credential_classes": ["read", "deploy"],
                "root_credential_present_by_design": False,
            },
            "audit": audit.verify(),
            "source_errors": source_errors,
        },
        max_chars=SETTINGS.max_response_chars,
    )


@mcp.resource(TEMPLATE_URI, "Veklom Operator Evidence Plane", mime_type=MIME_TYPE)
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
