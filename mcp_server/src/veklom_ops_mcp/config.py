from __future__ import annotations

import json
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
    docker_gate_url: str
    docker_gate_read_token: str | None
    docker_gate_act_token: str | None
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
    profile: str = "generic"
    approval_audience: str | None = None
    policy_file: Path | None = None
    audit_anchor_url: str | None = None
    audit_anchor_token: str | None = None
    health_targets_json: str | None = None
    security_posture_url: str | None = None
    approver_url: str | None = None
    public_url: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            service_name=os.getenv("VEKLOM_MCP_SERVICE_NAME", "Veklom Ops MCP"),
            environment=os.getenv("VEKLOM_MCP_ENVIRONMENT", "production"),
            docker_gate_url=os.getenv("DOCKER_GATE_URL", "http://docker-gate:8788").rstrip("/"),
            docker_gate_read_token=os.getenv("DOCKER_GATE_READ_TOKEN") or None,
            docker_gate_act_token=os.getenv("DOCKER_GATE_ACT_TOKEN") or None,
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
            profile=os.getenv("VEKLOM_MCP_PROFILE", "generic").strip().lower(),
            approval_audience=(os.getenv("VEKLOM_MCP_APPROVAL_AUDIENCE") or "").strip() or None,
            policy_file=Path(os.environ["VEKLOM_MCP_POLICY_FILE"]) if os.getenv("VEKLOM_MCP_POLICY_FILE") else None,
            audit_anchor_url=(os.getenv("VEKLOM_MCP_AUDIT_ANCHOR_URL") or "").strip() or None,
            audit_anchor_token=os.getenv("VEKLOM_MCP_AUDIT_ANCHOR_TOKEN") or None,
            health_targets_json=os.getenv("VEKLOM_MCP_HEALTH_TARGETS") or None,
            security_posture_url=(os.getenv("VEKLOM_MCP_SECURITY_POSTURE_URL") or "").strip() or None,
            approver_url=(os.getenv("VEKLOM_MCP_APPROVER_URL") or "").strip() or None,
            public_url=(os.getenv("VEKLOM_MCP_PUBLIC_URL") or "").strip().rstrip("/") or None,
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
                    ("DOCKER_GATE_ACT_TOKEN", self.docker_gate_act_token),
                    ("VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64", self.approval_public_key_b64),
                    ("VEKLOM_MCP_APPROVAL_AUDIENCE", self.approval_audience),
                )
                if not value
            ]
            if missing:
                raise RuntimeError(
                    f"Write mode is fail-closed; missing required settings: {', '.join(missing)}"
                )
            if self.docker_gate_read_token and self.docker_gate_read_token == self.docker_gate_act_token:
                raise RuntimeError("Docker gate read and act tokens must be different credentials.")

        for label, url in (
            ("DOCKER_GATE_URL", self.docker_gate_url),
            ("VEKLOM_BYOS_BASE_URL", self.byos_base_url),
            ("VEKLOM_CAPPO_BASE_URL", self.cappo_base_url),
            ("VEKLOM_PGL_BASE_URL", self.pgl_base_url),
            ("VEKLOM_CAPI_BASE_URL", self.capi_base_url),
            ("VEKLOM_CONTROL_BASE_URL", self.control_base_url),
        ):
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                raise RuntimeError(f"{label} must use HTTP(S), not {parsed.scheme or 'an empty scheme'}.")

        if self.profile not in {"generic", "veklom"}:
            raise RuntimeError("VEKLOM_MCP_PROFILE must be 'generic' or 'veklom'.")
        for label, url in (
            ("VEKLOM_MCP_AUDIT_ANCHOR_URL", self.audit_anchor_url),
            ("VEKLOM_MCP_SECURITY_POSTURE_URL", self.security_posture_url),
            ("VEKLOM_MCP_APPROVER_URL", self.approver_url),
            ("VEKLOM_MCP_PUBLIC_URL", self.public_url),
        ):
            if url and urlparse(url).scheme not in {"http", "https"}:
                raise RuntimeError(f"{label} must use HTTP(S).")
        if self.approver_url and self.public_url and self.approver_origin == _origin(self.public_url):
            raise RuntimeError(
                "VEKLOM_MCP_APPROVER_URL must be a different origin from the MCP: a page served by the MCP "
                "could use the approver's signing key if the MCP were compromised."
            )
        _ = self.health_targets  # Fail at startup on a malformed VEKLOM_MCP_HEALTH_TARGETS.

    @property
    def approver_origin(self) -> str | None:
        return _origin(self.approver_url) if self.approver_url else None

    @property
    def posture_url(self) -> str | None:
        if self.security_posture_url:
            return self.security_posture_url
        if self.profile == "veklom":
            return f"{self.byos_base_url}/api/v1/security/posture"
        return None

    @property
    def health_targets(self) -> dict[str, tuple[str, tuple[str, ...]]]:
        """Public health probes. VEKLOM_MCP_HEALTH_TARGETS wins; the veklom profile keeps the legacy targets."""
        if self.health_targets_json:
            return parse_health_targets(self.health_targets_json)
        if self.profile != "veklom":
            return {}
        return {
            "byos": (self.byos_base_url, ("/health", "/api/v1/health")),
            "cappo": (self.cappo_base_url, ("/health", "/health/detailed")),
            "pgl": (self.pgl_base_url, ("/health",)),
            "capi": (self.capi_base_url, ("/health",)),
            # The legacy Control Plane is not a Core V1 surface (CURRENT_ARCHITECTURE_LOCK.md); it is not probed.
        }


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".lower()


def parse_health_targets(raw: str) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Accept {"name": "https://host"} or {"name": {"base_url": "https://host", "paths": ["/health"]}}."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("VEKLOM_MCP_HEALTH_TARGETS must be a JSON object.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("VEKLOM_MCP_HEALTH_TARGETS must be a JSON object.")
    targets: dict[str, tuple[str, tuple[str, ...]]] = {}
    for name, spec in data.items():
        if isinstance(spec, str):
            base, paths = spec, ["/health"]
        elif isinstance(spec, dict) and isinstance(spec.get("base_url"), str):
            base, paths = spec["base_url"], spec.get("paths") or ["/health"]
        else:
            raise RuntimeError(f"Health target {name!r} must be a URL string or an object with base_url.")
        if urlparse(base).scheme not in {"http", "https"}:
            raise RuntimeError(f"Health target {name!r} must use HTTP(S).")
        if not isinstance(paths, list) or not all(isinstance(p, str) and p.startswith("/") for p in paths):
            raise RuntimeError(f"Health target {name!r} paths must be a list of absolute paths.")
        targets[str(name)] = (base.rstrip("/"), tuple(paths))
    return targets


SETTINGS = Settings.from_env()
