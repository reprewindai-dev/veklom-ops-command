from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _csv(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    service_name: str
    environment: str
    coolify_base_url: str
    coolify_read_token: str | None
    coolify_deploy_token: str | None
    byos_base_url: str
    cappo_base_url: str
    pgl_base_url: str
    capi_base_url: str
    control_base_url: str
    lockerphycer_base_url: str | None
    request_timeout_seconds: float
    max_log_lines: int
    max_response_chars: int
    writes_enabled: bool
    approval_ttl_seconds: int
    approval_store: Path
    audit_store: Path
    approval_public_key_b64: str | None
    access_token: str | None
    allow_unauthenticated: bool
    allowed_hosts: list[str]
    allowed_origins: list[str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            service_name=os.getenv("VEKLOM_MCP_SERVICE_NAME", "Veklom Ops MCP"),
            environment=os.getenv("VEKLOM_MCP_ENVIRONMENT", "production"),
            coolify_base_url=os.getenv("COOLIFY_BASE_URL", "http://host.docker.internal:8000").rstrip("/"),
            coolify_read_token=os.getenv("COOLIFY_READ_TOKEN"),
            coolify_deploy_token=os.getenv("COOLIFY_DEPLOY_TOKEN"),
            byos_base_url=os.getenv("VEKLOM_BYOS_BASE_URL", "https://api.veklom.com").rstrip("/"),
            cappo_base_url=os.getenv("VEKLOM_CAPPO_BASE_URL", "https://cappo.veklom.com").rstrip("/"),
            pgl_base_url=os.getenv("VEKLOM_PGL_BASE_URL", "https://pgl.veklom.com").rstrip("/"),
            capi_base_url=os.getenv("VEKLOM_CAPI_BASE_URL", "https://capi.veklom.com").rstrip("/"),
            control_base_url=os.getenv("VEKLOM_CONTROL_BASE_URL", "https://control.veklom.com").rstrip("/"),
            lockerphycer_base_url=(os.getenv("VEKLOM_LOCKERPHYCER_BASE_URL") or "").rstrip("/") or None,
            request_timeout_seconds=float(os.getenv("VEKLOM_MCP_REQUEST_TIMEOUT", "12")),
            max_log_lines=max(1, min(_int("VEKLOM_MCP_MAX_LOG_LINES", 200), 500)),
            max_response_chars=max(10_000, min(_int("VEKLOM_MCP_MAX_RESPONSE_CHARS", 120_000), 500_000)),
            writes_enabled=_bool("VEKLOM_MCP_WRITES_ENABLED", False),
            approval_ttl_seconds=max(60, min(_int("VEKLOM_MCP_APPROVAL_TTL_SECONDS", 600), 3600)),
            approval_store=Path(os.getenv("VEKLOM_MCP_APPROVAL_STORE", "/data/veklom-mcp/approvals.jsonl")),
            audit_store=Path(os.getenv("VEKLOM_MCP_AUDIT_STORE", "/data/veklom-mcp/audit.jsonl")),
            approval_public_key_b64=os.getenv("VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64"),
            access_token=os.getenv("VEKLOM_MCP_ACCESS_TOKEN"),
            allow_unauthenticated=_bool("VEKLOM_MCP_ALLOW_UNAUTHENTICATED", False),
            allowed_hosts=_csv("MCP_ALLOWED_HOSTS"),
            allowed_origins=_csv("MCP_ALLOWED_ORIGINS"),
        )

    def validate(self) -> None:
        if not self.allow_unauthenticated and not self.access_token:
            raise RuntimeError(
                "Inbound MCP authentication is required. Set VEKLOM_MCP_ACCESS_TOKEN, "
                "or explicitly set VEKLOM_MCP_ALLOW_UNAUTHENTICATED=true only behind a private/tunneled boundary."
            )
        if self.writes_enabled:
            missing = [
                name
                for name, value in (
                    ("COOLIFY_DEPLOY_TOKEN", self.coolify_deploy_token),
                    ("VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64", self.approval_public_key_b64),
                )
                if not value
            ]
            if missing:
                raise RuntimeError(
                    f"Write mode is fail-closed; missing required settings: {', '.join(missing)}"
                )
            if self.coolify_read_token and self.coolify_read_token == self.coolify_deploy_token:
                raise RuntimeError("Read and deploy Coolify tokens must be different credentials.")

        for label, url in (
            ("COOLIFY_BASE_URL", self.coolify_base_url),
            ("VEKLOM_BYOS_BASE_URL", self.byos_base_url),
            ("VEKLOM_CAPPO_BASE_URL", self.cappo_base_url),
            ("VEKLOM_PGL_BASE_URL", self.pgl_base_url),
            ("VEKLOM_CAPI_BASE_URL", self.capi_base_url),
            ("VEKLOM_CONTROL_BASE_URL", self.control_base_url),
        ):
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                raise RuntimeError(f"{label} must use HTTP(S), not {parsed.scheme or 'an empty scheme'}.")

    @property
    def health_targets(self) -> dict[str, tuple[str, tuple[str, ...]]]:
        return {
            "byos": (self.byos_base_url, ("/health", "/api/v1/health")),
            "cappo": (self.cappo_base_url, ("/health", "/health/detailed")),
            "pgl": (self.pgl_base_url, ("/health",)),
            "capi": (self.capi_base_url, ("/health",)),
            "control": (self.control_base_url, ("/",)),
        }


SETTINGS = Settings.from_env()
