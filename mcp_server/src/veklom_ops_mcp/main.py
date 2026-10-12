from __future__ import annotations

import hashlib
import html
import hmac
import json
from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .approval import ApprovalError
from .config import SETTINGS
from .tools import audit, inbox, mcp
from . import app_ui as _app_ui  # noqa: F401  Registers MCP App resource/tools.
from .tool_annotations import apply_tool_annotations

MAX_REQUEST_BYTES = 1_048_576
DELIVER_PATH = "/approvals/deliver"
PUBLIC_PATHS = {"/health", "/", "/favicon.ico"}


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
        if path in PUBLIC_PATHS and scope.get("method") in {"GET", "HEAD"}:
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        if path == DELIVER_PATH:
            # Self-authenticating: only a token signed by the approver's key is accepted, so no bearer
            # is required. Browser access is limited to the configured approver origin.
            origin = headers.get("origin")
            if origin and origin.lower() != (SETTINGS.approver_origin or ""):
                response = PlainTextResponse("Origin not allowed", status_code=403)
                await response(scope, receive, send)
                return
            if SETTINGS.allowed_hosts and _host_without_port(headers.get("host", "")) not in {h.lower() for h in SETTINGS.allowed_hosts}:
                response = PlainTextResponse("Host not allowed", status_code=403)
                await response(scope, receive, send)
                return
            await self.app(scope, receive, send)
            return
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


def _cors_headers() -> dict[str, str]:
    if not SETTINGS.approver_origin:
        return {}
    return {
        "Access-Control-Allow-Origin": SETTINGS.approver_origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


@mcp.custom_route(DELIVER_PATH, methods=["POST", "OPTIONS"])
async def deliver_approval(request: Request) -> JSONResponse:
    """Accept an approval signed on a human's device and hold it for the exact call it names."""
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=_cors_headers())
    body = await request.body()
    if len(body) > 8192:
        return JSONResponse({"delivered": False, "error": "Request too large."}, status_code=413, headers=_cors_headers())
    try:
        token = str(json.loads(body).get("token", ""))
    except (ValueError, AttributeError):
        return JSONResponse({"delivered": False, "error": "Body must be JSON with a token."}, status_code=400, headers=_cors_headers())
    try:
        result = inbox.deliver(token)
    except ApprovalError as exc:
        audit.append(tool="deliver_approval", action="approval.deliver", risk_tier="high", outcome="denied", request={"token_sha256": hashlib.sha256(token.encode()).hexdigest()}, reason=str(exc))
        return JSONResponse({"delivered": False, "error": str(exc)}, status_code=400, headers=_cors_headers())
    audit.append(tool="deliver_approval", action="approval.deliver", risk_tier="high", outcome="success", request={"request_id": result["request_id"]}, approved_by=result["approved_by"])
    return JSONResponse(result, headers=_cors_headers())


@mcp.custom_route("/", methods=["GET"])
async def landing(_: Request) -> HTMLResponse:
    """A person who opens the server address sees what it is, not a bare 401. Reveals no operational state."""
    approver = html.escape(SETTINGS.approver_url or "")
    link = (
        f"<p>To approve what your agent asks for, open your <a href=\"{approver}\">approval page</a>.</p>"
        if approver
        else "<p>Approvals are signed with the <code>veklom-mcp-approve</code> tool.</p>"
    )
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1\">"
        "<title>Veklom Gate server</title>"
        "<body style=\"font:16px/1.5 system-ui,sans-serif;max-width:560px;margin:12vh auto;padding:0 20px\">"
        "<h1 style=\"font-size:22px\">Veklom Gate server is running</h1>"
        "<p>This address is for AI agents. They connect at <code>/mcp</code> with their access token; "
        "there is nothing to do here in a browser.</p>"
        f"{link}</body>",
        headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"},
    )


@mcp.custom_route("/favicon.ico", methods=["GET"])
async def favicon(_: Request) -> Response:
    return Response(status_code=204)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    # Keep unauthenticated liveness intentionally minimal. Operational authority
    # state is available only through authenticated MCP tools.
    return JSONResponse({"status": "ok", "service": "veklom-ops-mcp"})


SETTINGS.validate()
apply_tool_annotations(mcp)
app: Any = InboundSecurityMiddleware(mcp.streamable_http_app())
