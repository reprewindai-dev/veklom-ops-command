from __future__ import annotations

import hmac
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import SETTINGS
from .tools import mcp
from . import app_ui as _app_ui  # noqa: F401  Registers MCP App resource/tools.
from .tool_annotations import apply_tool_annotations

MAX_REQUEST_BYTES = 1_048_576


def _host_without_port(host: str) -> str:
    host = host.strip().lower()
    if host.startswith("[") and "]" in host:
        return host[1 : host.index("]")]
    if host.count(":") == 1:
        return host.split(":", 1)[0]
    return host


class InboundSecurityMiddleware:
    """Separate ChatGPT/client auth from upstream infrastructure credentials."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        if path == "/health":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        # Do not trust X-Forwarded-Host supplied by an arbitrary client. Traefik
        # preserves the external Host header for the upstream application.
        host = _host_without_port(headers.get("host", ""))
        origin = headers.get("origin")
        content_length = headers.get("content-length")

        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    response = PlainTextResponse("Request too large", status_code=413)
                    await response(scope, receive, send)
                    return
            except ValueError:
                response = PlainTextResponse("Invalid Content-Length", status_code=400)
                await response(scope, receive, send)
                return

        if SETTINGS.allowed_hosts and host not in {item.lower() for item in SETTINGS.allowed_hosts}:
            response = PlainTextResponse("Host not allowed", status_code=403)
            await response(scope, receive, send)
            return
        if origin and SETTINGS.allowed_origins and origin not in SETTINGS.allowed_origins:
            response = PlainTextResponse("Origin not allowed", status_code=403)
            await response(scope, receive, send)
            return

        if not SETTINGS.allow_unauthenticated:
            presented = headers.get("authorization", "")
            expected = f"Bearer {SETTINGS.access_token}"
            if not hmac.compare_digest(presented, expected):
                response = PlainTextResponse(
                    "Unauthorized", status_code=401, headers={"WWW-Authenticate": "Bearer"}
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    # Keep unauthenticated liveness intentionally minimal. Operational authority
    # state is available only through authenticated MCP tools.
    return JSONResponse({"status": "ok", "service": "veklom-ops-mcp"})


SETTINGS.validate()
apply_tool_annotations(mcp)
app: Any = InboundSecurityMiddleware(mcp.streamable_http_app())
