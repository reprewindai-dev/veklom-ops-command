from __future__ import annotations

import hmac
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import SETTINGS
from .tools import mcp


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
        host = headers.get("x-forwarded-host") or headers.get("host", "")
        origin = headers.get("origin")

        if SETTINGS.allowed_hosts and host not in SETTINGS.allowed_hosts:
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
                response = PlainTextResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Bearer"})
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "service": SETTINGS.service_name,
            "environment": SETTINGS.environment,
            "mcp": "ready",
            "writes_enabled": SETTINGS.writes_enabled,
            "database_writes": False,
            "arbitrary_shell": False,
        }
    )


SETTINGS.validate()
app: Any = InboundSecurityMiddleware(mcp.streamable_http_app())
