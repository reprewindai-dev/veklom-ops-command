"""Docker gate: the only process that holds the Docker socket.

Access to the Docker socket is root on the host. The MCP server therefore never receives it.
This small service holds the socket and exposes a fixed capability ceiling over HTTP:

    read  : host info, list/inspect managed containers, env-var NAMES, capped redacted logs
    act   : restart / stop / start a managed container (off unless DOCKER_GATE_ALLOW_ACT=true)

There is no route for exec, create, remove, attach, archive, volumes, images, networks, build,
prune or env values, so no policy decision or approval upstream can reach them. Only containers
carrying the opt-in label (default veklom.ops.managed=true) are visible or actionable.
"""
from __future__ import annotations

import hmac
import json
import os
import re
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .redaction import redact
from .safe_projection import container_detail, container_summary, env_names, host_info

CONTAINER_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
MAX_LOG_LINES = 500
MAX_LOG_CHARS = 120_000


@dataclass(frozen=True)
class GateSettings:
    socket_path: str
    read_token: str | None
    act_token: str | None
    allow_act: bool
    managed_label: str
    stop_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "GateSettings":
        return cls(
            socket_path=os.getenv("DOCKER_GATE_SOCKET", "/var/run/docker.sock"),
            read_token=os.getenv("DOCKER_GATE_READ_TOKEN") or None,
            act_token=os.getenv("DOCKER_GATE_ACT_TOKEN") or None,
            allow_act=os.getenv("DOCKER_GATE_ALLOW_ACT", "false").strip().lower() in {"1", "true", "yes", "on"},
            managed_label=os.getenv("DOCKER_GATE_MANAGED_LABEL", "veklom.ops.managed=true"),
            stop_timeout_seconds=max(1, min(int(os.getenv("DOCKER_GATE_STOP_TIMEOUT", "30")), 300)),
        )

    def validate(self) -> None:
        if not self.read_token:
            raise RuntimeError("DOCKER_GATE_READ_TOKEN is required.")
        if self.allow_act and not self.act_token:
            raise RuntimeError("DOCKER_GATE_ALLOW_ACT=true requires DOCKER_GATE_ACT_TOKEN.")
        if self.act_token and hmac.compare_digest(self.act_token, self.read_token):
            raise RuntimeError("Read and act tokens must be different credentials.")
        if "=" not in self.managed_label:
            raise RuntimeError("DOCKER_GATE_MANAGED_LABEL must be key=value.")

    @property
    def label_key_value(self) -> tuple[str, str]:
        key, value = self.managed_label.split("=", 1)
        return key, value


class GateError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class DockerEngine:
    """Minimal Docker Engine API client over the unix socket. Only the calls listed here exist."""

    def __init__(self, settings: GateSettings, transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None):
        self.settings = settings
        self.transport_factory = transport_factory

    async def _call(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        # A fresh socket transport per call: closing a shared one would abort concurrent inspects.
        transport = self.transport_factory() if self.transport_factory else httpx.AsyncHTTPTransport(uds=self.settings.socket_path)
        async with httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=60.0) as client:
            response = await client.request(method, path, params=params)
        if response.status_code == 404:
            raise GateError(404, "Container not found or not managed.")
        if response.status_code >= 400 and response.status_code != 304:
            raise GateError(502, f"Docker Engine {method} {path.split('/')[1]} failed ({response.status_code}).")
        return response

    async def list_managed(self) -> list[dict[str, Any]]:
        filters = json.dumps({"label": [self.settings.managed_label]})
        response = await self._call("GET", "/containers/json", params={"all": "1", "filters": filters})
        rows = response.json()
        return rows if isinstance(rows, list) else []

    async def inspect_managed(self, ref: str) -> dict[str, Any]:
        if not CONTAINER_REF.match(ref):
            raise GateError(400, "Invalid container reference.")
        raw = (await self._call("GET", f"/containers/{ref}/json")).json()
        key, value = self.settings.label_key_value
        labels = (raw.get("Config") or {}).get("Labels") or {} if isinstance(raw, dict) else {}
        if labels.get(key) != value:
            # Identical to "missing" so unmanaged containers cannot be enumerated through the gate.
            raise GateError(404, "Container not found or not managed.")
        return raw

    async def logs(self, container_id: str, tail: int, tty: bool) -> str:
        response = await self._call(
            "GET", f"/containers/{container_id}/logs", params={"stdout": "1", "stderr": "1", "tail": str(tail), "timestamps": "1"}
        )
        data = response.content if tty else demux_log_stream(response.content)
        return data.decode("utf-8", errors="replace")

    async def lifecycle(self, container_id: str, verb: str) -> None:
        params = {"t": str(self.settings.stop_timeout_seconds)} if verb in {"stop", "restart"} else None
        await self._call("POST", f"/containers/{container_id}/{verb}", params=params)

    async def host(self) -> dict[str, Any]:
        info = (await self._call("GET", "/info")).json()
        version = (await self._call("GET", "/version")).json()
        return host_info(info, version)


def demux_log_stream(data: bytes) -> bytes:
    """Strip Docker's 8-byte multiplexing headers from a non-TTY log stream."""
    out = bytearray()
    index = 0
    while index + 8 <= len(data):
        size = int.from_bytes(data[index + 4 : index + 8], "big")
        if data[index] not in (0, 1, 2) or data[index + 1 : index + 4] != b"\x00\x00\x00":
            return data  # Not a multiplexed stream; return as-is.
        out += data[index + 8 : index + 8 + size]
        index += 8 + size
    return bytes(out)


def build_app(settings: GateSettings | None = None, transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None) -> Starlette:
    settings = settings or GateSettings.from_env()
    settings.validate()
    engine = DockerEngine(settings, transport_factory)

    def authorize(request: Request, scope: str) -> None:
        presented = request.headers.get("authorization", "")
        token = settings.read_token if scope == "read" else settings.act_token
        if scope == "act" and not settings.allow_act:
            raise GateError(403, "Lifecycle actions are disabled on this gate (DOCKER_GATE_ALLOW_ACT=false).")
        if not token or not hmac.compare_digest(presented, f"Bearer {token}"):
            raise GateError(401, "Unauthorized.")

    def handler(scope: str, fn):
        async def endpoint(request: Request) -> JSONResponse:
            try:
                authorize(request, scope)
                return JSONResponse(await fn(request))
            except GateError as exc:
                return JSONResponse({"error": exc.message}, status_code=exc.status)
            except httpx.HTTPError:
                return JSONResponse({"error": "Docker Engine unreachable."}, status_code=502)

        return endpoint

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "veklom-docker-gate"})

    async def host(_: Request) -> dict[str, Any]:
        return await engine.host()

    async def containers(_: Request) -> list[dict[str, Any]]:
        return [container_summary(row) for row in await engine.list_managed()]

    async def container(request: Request) -> dict[str, Any]:
        return container_detail(await engine.inspect_managed(request.path_params["ref"]))

    async def container_env_names(request: Request) -> dict[str, Any]:
        raw = await engine.inspect_managed(request.path_params["ref"])
        return {"id": raw.get("Id"), "env_names": env_names(raw)}

    async def container_logs(request: Request) -> dict[str, Any]:
        raw = await engine.inspect_managed(request.path_params["ref"])
        try:
            tail = int(request.query_params.get("tail", "100"))
        except ValueError as exc:
            raise GateError(400, "tail must be an integer.") from exc
        tail = max(1, min(tail, MAX_LOG_LINES))
        text = await engine.logs(raw["Id"], tail, bool((raw.get("Config") or {}).get("Tty")))
        return {"id": raw["Id"], "lines": tail, "logs": redact(text, max_chars=MAX_LOG_CHARS)}

    def lifecycle(verb: str):
        async def act(request: Request) -> dict[str, Any]:
            raw = await engine.inspect_managed(request.path_params["ref"])
            await engine.lifecycle(raw["Id"], verb)
            return {"id": raw["Id"], "accepted": verb}

        return act

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/v1/host", handler("read", host), methods=["GET"]),
        Route("/v1/containers", handler("read", containers), methods=["GET"]),
        Route("/v1/containers/{ref}", handler("read", container), methods=["GET"]),
        Route("/v1/containers/{ref}/env-names", handler("read", container_env_names), methods=["GET"]),
        Route("/v1/containers/{ref}/logs", handler("read", container_logs), methods=["GET"]),
        Route("/v1/containers/{ref}/restart", handler("act", lifecycle("restart")), methods=["POST"]),
        Route("/v1/containers/{ref}/stop", handler("act", lifecycle("stop")), methods=["POST"]),
        Route("/v1/containers/{ref}/start", handler("act", lifecycle("start")), methods=["POST"]),
    ]
    return Starlette(routes=routes)


def __getattr__(name: str) -> Any:
    # `uvicorn veklom_ops_mcp.docker_gate:app` builds the app lazily so importing this module in tests needs no env.
    if name == "app":
        return build_app()
    raise AttributeError(name)
