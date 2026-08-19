from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import SETTINGS, Settings
from .redaction import redact
from .safe_projection import project, project_domains


class UpstreamError(RuntimeError):
    pass


class CoolifyClient:
    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    async def _request(
        self,
        method: str,
        path: str,
        *,
        deploy: bool = False,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        token = self.settings.coolify_deploy_token if deploy else self.settings.coolify_read_token
        if not token:
            raise UpstreamError(f"Coolify {'deploy' if deploy else 'read'} credential is not configured.")
        url = f"{self.settings.coolify_base_url}/api/v1{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=False) as client:
            response = await client.request(method, url, headers=headers, params=params, json=json_body)
        if response.status_code >= 400:
            body = redact(response.text, max_chars=4000)
            raise UpstreamError(f"Coolify {method} {path} failed ({response.status_code}): {body}")
        if not response.content:
            return {"status_code": response.status_code}
        try:
            payload = response.json()
        except ValueError:
            payload = {"text": response.text}
        return redact(payload, max_chars=self.settings.max_response_chars)

    async def list_servers(self) -> Any:
        return project("server", await self._request("GET", "/servers"))

    async def get_server(self, uuid: str) -> Any:
        return project("server", await self._request("GET", f"/servers/{uuid}"))

    async def server_resources(self, uuid: str) -> Any:
        return project("server_resource", await self._request("GET", f"/servers/{uuid}/resources"))

    async def server_domains(self, uuid: str) -> Any:
        return project_domains(await self._request("GET", f"/servers/{uuid}/domains"))

    async def list_applications(self) -> Any:
        return project("application", await self._request("GET", "/applications"))

    async def get_application(self, uuid: str) -> Any:
        return project("application", await self._request("GET", f"/applications/{uuid}"))

    async def application_env_presence(self, uuid: str) -> Any:
        return project("environment_presence", await self._request("GET", f"/applications/{uuid}/envs"))

    async def application_logs(self, uuid: str, lines: int) -> Any:
        lines = max(1, min(lines, self.settings.max_log_lines))
        return redact(
            await self._request("GET", f"/applications/{uuid}/logs", params={"lines": lines}),
            max_chars=self.settings.max_response_chars,
        )

    async def list_databases(self) -> Any:
        return project("database", await self._request("GET", "/databases"))

    async def get_database(self, uuid: str) -> Any:
        return project("database", await self._request("GET", f"/databases/{uuid}"))

    async def database_backups(self, uuid: str) -> Any:
        return project("backup", await self._request("GET", f"/databases/{uuid}/backups"))

    async def list_services(self) -> Any:
        return project("service", await self._request("GET", "/services"))

    async def get_service(self, uuid: str) -> Any:
        return project("service", await self._request("GET", f"/services/{uuid}"))

    async def service_logs(self, uuid: str, lines: int) -> Any:
        lines = max(1, min(lines, self.settings.max_log_lines))
        return redact(
            await self._request("GET", f"/services/{uuid}/logs", params={"lines": lines}),
            max_chars=self.settings.max_response_chars,
        )

    async def list_deployments(self) -> Any:
        return project("deployment", await self._request("GET", "/deployments"))

    async def get_deployment(self, uuid: str) -> Any:
        return project("deployment", await self._request("GET", f"/deployments/{uuid}"))

    async def restart_application(self, uuid: str) -> Any:
        return await self._request("POST", f"/applications/{uuid}/restart", deploy=True)

    async def start_application(self, uuid: str) -> Any:
        return await self._request("POST", f"/applications/{uuid}/start", deploy=True)

    async def stop_application(self, uuid: str) -> Any:
        return await self._request("POST", f"/applications/{uuid}/stop", deploy=True)

    async def restart_service(self, uuid: str) -> Any:
        return await self._request("POST", f"/services/{uuid}/restart", deploy=True)

    async def start_service(self, uuid: str) -> Any:
        return await self._request("POST", f"/services/{uuid}/start", deploy=True)

    async def stop_service(self, uuid: str) -> Any:
        return await self._request("POST", f"/services/{uuid}/stop", deploy=True)

    async def deploy(self, uuid: str, *, force: bool = False) -> Any:
        return await self._request("POST", "/deploy", deploy=True, json_body={"uuid": uuid, "force": force})

    async def cancel_deployment(self, uuid: str) -> Any:
        return await self._request("POST", f"/deployments/{uuid}/cancel", deploy=True)


class VeklomClient:
    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    async def _get(self, base: str, path: str) -> dict[str, Any]:
        url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
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
        result = await self._get(self.settings.byos_base_url, "/api/v1/security/posture")
        result["proof_state"] = "VERIFIED_LIVE" if result.get("ok") else "UNVERIFIED"
        return result
