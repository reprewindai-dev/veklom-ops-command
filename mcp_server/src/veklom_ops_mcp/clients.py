from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote, urljoin

import httpx

from .config import SETTINGS, Settings
from .redaction import redact
from .safe_projection import container_detail, container_summary, is_healthy


class UpstreamError(RuntimeError):
    pass


class DockerGateClient:
    """Talks to the socket-holding Docker gate. This process never touches the Docker socket.

    Reads use the gate's read token; lifecycle calls use its separate act token. Gate responses
    are re-projected here as defence in depth, so a gate bug cannot widen what reaches the agent.
    """

    def __init__(self, settings: Settings = SETTINGS, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    async def _request(self, method: str, path: str, *, act: bool = False, params: dict[str, Any] | None = None) -> Any:
        token = self.settings.docker_gate_act_token if act else self.settings.docker_gate_read_token
        if not token:
            raise UpstreamError(f"Docker gate {'act' if act else 'read'} credential is not configured.")
        url = f"{self.settings.docker_gate_url}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=self.settings.request_timeout_seconds + 60, follow_redirects=False) as client:
                response = await client.request(method, url, headers=headers, params=params)
        except httpx.HTTPError as exc:
            raise UpstreamError(f"Docker gate unreachable ({type(exc).__name__}).") from exc
        if response.status_code >= 400:
            raise UpstreamError(f"Docker gate {method} {path} failed ({response.status_code}): {redact(response.text, max_chars=2000)}")
        return redact(response.json(), max_chars=self.settings.max_response_chars)

    @staticmethod
    def _ref(container: str) -> str:
        return quote(container, safe="")

    async def host(self) -> Any:
        return await self._request("GET", "/v1/host")

    async def list_containers(self) -> list[dict[str, Any]]:
        rows = await self._request("GET", "/v1/containers")
        return [container_summary(_unproject_summary(row)) for row in rows] if isinstance(rows, list) else []

    async def get_container(self, container: str) -> dict[str, Any]:
        return _reproject_detail(await self._request("GET", f"/v1/containers/{self._ref(container)}"))

    async def container_env_names(self, container: str) -> Any:
        result = await self._request("GET", f"/v1/containers/{self._ref(container)}/env-names")
        names = result.get("env_names") if isinstance(result, dict) else None
        return {"id": result.get("id") if isinstance(result, dict) else None, "env_names": [str(n) for n in names] if isinstance(names, list) else []}

    async def container_logs(self, container: str, lines: int) -> Any:
        lines = max(1, min(lines, self.settings.max_log_lines))
        return await self._request("GET", f"/v1/containers/{self._ref(container)}/logs", params={"tail": lines})

    async def restart(self, container: str) -> Any:
        return await self._request("POST", f"/v1/containers/{self._ref(container)}/restart", act=True)

    async def stop(self, container: str) -> Any:
        return await self._request("POST", f"/v1/containers/{self._ref(container)}/stop", act=True)

    async def start(self, container: str) -> Any:
        return await self._request("POST", f"/v1/containers/{self._ref(container)}/start", act=True)

    async def service_replicas(self, detail: dict[str, Any]) -> dict[str, Any]:
        """Observe the compose service a container belongs to: how many replicas are running with a passing health check."""
        labels = detail.get("labels") or {}
        project, service = labels.get("com.docker.compose.project"), labels.get("com.docker.compose.service")
        if not project or not service:
            return {"service": None, "replicas": 1, "healthy_replicas": 1 if is_healthy(detail) else 0}
        siblings = [
            row["id"]
            for row in await self.list_containers()
            if row.get("id") and row["labels"].get("com.docker.compose.project") == project and row["labels"].get("com.docker.compose.service") == service
        ]
        details = await asyncio.gather(*(self.get_container(cid) for cid in siblings))
        return {
            "service": f"{project}/{service}",
            "replicas": len(details),
            "healthy_replicas": sum(1 for item in details if is_healthy(item)),
        }


def _unproject_summary(row: Any) -> dict[str, Any]:
    """Map the gate's projected summary back to Docker's shape so the shared allowlist is re-applied."""
    if not isinstance(row, dict):
        return {}
    return {
        "Id": row.get("id"),
        "Names": [row["name"]] if row.get("name") else [],
        "Image": row.get("image"),
        "ImageID": row.get("image_id"),
        "State": row.get("state"),
        "Status": row.get("status"),
        "Created": row.get("created"),
        "Labels": row.get("labels"),
    }


def _reproject_detail(detail: Any) -> dict[str, Any]:
    if not isinstance(detail, dict):
        return {}
    state = detail.get("state") if isinstance(detail.get("state"), dict) else {}
    return container_detail(
        {
            "Id": detail.get("id"),
            "Name": detail.get("name") or "",
            "Created": detail.get("created"),
            "Image": detail.get("image_id"),
            "RestartCount": detail.get("restart_count"),
            "HostConfig": {"RestartPolicy": {"Name": detail.get("restart_policy")}},
            "Config": {
                "Image": detail.get("image"),
                "Tty": detail.get("tty"),
                "Labels": detail.get("labels"),
                "Healthcheck": {"Test": ["CMD"] if detail.get("has_healthcheck") else ["NONE"]},
            },
            "State": {
                "Status": state.get("status"),
                "Running": state.get("running"),
                "Restarting": state.get("restarting"),
                "OOMKilled": state.get("oom_killed"),
                "ExitCode": state.get("exit_code"),
                "StartedAt": state.get("started_at"),
                "FinishedAt": state.get("finished_at"),
                "Health": {"Status": state.get("health"), "FailingStreak": state.get("failing_streak")},
            },
        }
    )


class VeklomClient:
    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    async def _get(self, base: str, path: str) -> dict[str, Any]:
        url = urljoin(base.rstrip("/") + "/", path.lstrip("/")) if path else base
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=False) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                body: Any = response.json()
            else:
                body = response.text[:4000]
            return {
                "url": url,
                "status_code": response.status_code,
                "ok": 200 <= response.status_code < 300,
                "reachable": 200 <= response.status_code < 400,
                "redirect_location": response.headers.get("location") if 300 <= response.status_code < 400 else None,
                "body": redact(body, max_chars=20_000),
            }
        except Exception as exc:
            return {
                "url": url,
                "status_code": None,
                "ok": False,
                "reachable": False,
                "error": type(exc).__name__,
            }

    async def health_matrix(self) -> dict[str, Any]:
        async def check(name: str, base: str, paths: tuple[str, ...]) -> tuple[str, dict[str, Any]]:
            attempts: list[dict[str, Any]] = []
            for path in paths:
                result = await self._get(base, path)
                attempts.append(result)
                if result.get("ok"):
                    return name, {"state": "VERIFIED_LIVE", "selected": result, "attempts": attempts}
            selected = attempts[-1] if attempts else None
            state = "REACHABLE_UNVERIFIED" if any(item.get("reachable") for item in attempts) else "UNVERIFIED"
            return name, {"state": state, "selected": selected, "attempts": attempts}

        rows = await asyncio.gather(
            *(check(name, base, paths) for name, (base, paths) in self.settings.health_targets.items())
        )
        return dict(rows)

    async def security_posture(self) -> dict[str, Any]:
        url = self.settings.posture_url
        if not url:
            return {"ok": False, "proof_state": "NOT_CONFIGURED", "hint": "Set VEKLOM_MCP_SECURITY_POSTURE_URL."}
        result = await self._get(url, "")
        result["proof_state"] = "VERIFIED_LIVE" if result.get("ok") else "UNVERIFIED"
        return result
