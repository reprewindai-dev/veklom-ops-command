"""In-process fake of the Docker Engine API endpoints the gate is allowed to call. Records every request."""
from __future__ import annotations

import json
import re

import httpx

MANAGED = {"veklom.ops.managed": "true"}


def container(cid, name, *, service="web", project="shop", health="healthy", running=True, managed=True, tty=False, extra_labels=None, env=None):
    labels = {"com.docker.compose.project": project, "com.docker.compose.service": service}
    if managed:
        labels.update(MANAGED)
    labels.update(extra_labels or {})
    return {
        "Id": cid,
        "Name": "/" + name,
        "Created": "2026-10-01T00:00:00Z",
        "Image": "sha256:" + "a" * 64,
        "RestartCount": 0,
        "Args": ["--password", "hunter2"],
        "Mounts": [{"Source": "/srv/secrets", "Destination": "/run/secrets"}],
        "HostConfig": {"RestartPolicy": {"Name": "unless-stopped"}, "Privileged": False},
        "Config": {
            "Image": "shop/web:1.4.2",
            "Tty": tty,
            "Labels": labels,
            "Env": env if env is not None else ["DATABASE_URL=postgres://app:s3cr3t@db/app", "PORT=8080"],
            "Healthcheck": {"Test": ["CMD", "curl", "-f", "http://localhost/health"]} if health else {"Test": ["NONE"]},
        },
        "State": {
            "Status": "running" if running else "exited",
            "Running": running,
            "Restarting": False,
            "OOMKilled": False,
            "ExitCode": 0,
            "StartedAt": "2026-10-01T00:00:00Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
            "Health": {"Status": health, "FailingStreak": 0, "Log": [{"Output": "token=abc123"}]} if health else None,
        },
    }


def frame(stream: int, payload: bytes) -> bytes:
    return bytes([stream, 0, 0, 0]) + len(payload).to_bytes(4, "big") + payload


class FakeDocker:
    def __init__(self, containers):
        self.containers = {c["Id"]: c for c in containers}
        self.requests: list[tuple[str, str]] = []
        self.logs = frame(1, b"2026-10-11T00:00:00Z started on :8080\n") + frame(2, b"2026-10-11T00:00:01Z auth password=hunter2\n")

    def _find(self, ref):
        for c in self.containers.values():
            if c["Id"] == ref or c["Id"].startswith(ref) or c["Name"].lstrip("/") == ref:
                return c
        return None

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.requests.append((request.method, path))
        if request.method == "GET" and path == "/containers/json":
            filters = json.loads(request.url.params.get("filters", "{}"))
            wanted = filters.get("label", [])
            rows = []
            for c in self.containers.values():
                labels = c["Config"]["Labels"]
                if all(labels.get(k) == v for k, v in (item.split("=", 1) for item in wanted)):
                    rows.append({
                        "Id": c["Id"], "Names": [c["Name"]], "Image": c["Config"]["Image"], "ImageID": c["Image"],
                        "State": c["State"]["Status"], "Status": "Up 1 hour" + (f" ({c['State']['Health']['Status']})" if c["State"]["Health"] else ""),
                        "Created": 1, "Labels": labels,
                    })
            return httpx.Response(200, json=rows)
        if request.method == "GET" and path in {"/info", "/version"}:
            if path == "/info":
                return httpx.Response(200, json={"Name": "box1", "ServerVersion": "27.3.1", "OperatingSystem": "Debian", "Containers": 3, "RegistryConfig": {"secret": "x"}})
            return httpx.Response(200, json={"Version": "27.3.1", "ApiVersion": "1.47"})
        match = re.fullmatch(r"/containers/([^/]+)/(json|logs|restart|stop|start)", path)
        if match:
            c = self._find(match.group(1))
            if c is None:
                return httpx.Response(404, json={"message": "No such container"})
            verb = match.group(2)
            if verb == "json" and request.method == "GET":
                return httpx.Response(200, json=c)
            if verb == "logs" and request.method == "GET":
                return httpx.Response(200, content=self.logs)
            if request.method == "POST":
                return httpx.Response(204)
        return httpx.Response(500, json={"message": f"fake docker: unexpected {request.method} {path}"})

    def transport(self) -> httpx.MockTransport:
        return ClosingMockTransport(self.handler)


class ClosingMockTransport(httpx.MockTransport):
    """Behaves like a real pooled transport: once closed, it refuses further requests."""

    closed = False

    async def handle_async_request(self, request):
        if self.closed:
            raise httpx.ConnectError("transport closed")
        return await super().handle_async_request(request)

    async def aclose(self) -> None:
        self.closed = True
