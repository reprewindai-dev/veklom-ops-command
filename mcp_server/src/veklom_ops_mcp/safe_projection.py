"""Allowlisted views of Docker Engine objects.

A field reaches an MCP client only if it is named here. Container env values, mounts, health-check
output, arbitrary labels (which often carry auth hashes or tokens) and archive data are never projected.
"""
from __future__ import annotations

import re
from typing import Any

LABEL_ALLOWLIST = (
    "com.docker.compose.project",
    "com.docker.compose.service",
    "com.docker.compose.container-number",
    "com.docker.compose.oneoff",
)
LABEL_PREFIX_ALLOWLIST = ("veklom.ops.",)

_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def safe_labels(labels: Any) -> dict[str, str]:
    if not isinstance(labels, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in labels.items()
        if key in LABEL_ALLOWLIST or any(str(key).startswith(prefix) for prefix in LABEL_PREFIX_ALLOWLIST)
    }


def container_summary(row: Any) -> dict[str, Any]:
    """Project one entry of GET /containers/json."""
    if not isinstance(row, dict):
        return {}
    names = row.get("Names") if isinstance(row.get("Names"), list) else []
    return {
        "id": row.get("Id"),
        "name": str(names[0]).lstrip("/") if names else None,
        "image": row.get("Image"),
        "image_id": row.get("ImageID"),
        "state": row.get("State"),
        "status": row.get("Status"),
        "created": row.get("Created"),
        "labels": safe_labels(row.get("Labels")),
    }


def container_detail(raw: Any) -> dict[str, Any]:
    """Project GET /containers/{id}/json without Env, Mounts, Args, health-check output or network secrets."""
    if not isinstance(raw, dict):
        return {}
    state = raw.get("State") if isinstance(raw.get("State"), dict) else {}
    health = state.get("Health") if isinstance(state.get("Health"), dict) else {}
    config = raw.get("Config") if isinstance(raw.get("Config"), dict) else {}
    host_config = raw.get("HostConfig") if isinstance(raw.get("HostConfig"), dict) else {}
    restart_policy = host_config.get("RestartPolicy") if isinstance(host_config.get("RestartPolicy"), dict) else {}
    healthcheck = config.get("Healthcheck") if isinstance(config.get("Healthcheck"), dict) else {}
    test = healthcheck.get("Test") if isinstance(healthcheck.get("Test"), list) else []
    return {
        "id": raw.get("Id"),
        "name": str(raw.get("Name", "")).lstrip("/") or None,
        "created": raw.get("Created"),
        "image": config.get("Image"),
        "image_id": raw.get("Image"),
        "restart_count": raw.get("RestartCount"),
        "restart_policy": restart_policy.get("Name"),
        "tty": bool(config.get("Tty", False)),
        "has_healthcheck": bool(test) and test[0] != "NONE",
        "labels": safe_labels(config.get("Labels")),
        "state": {
            "status": state.get("Status"),
            "running": state.get("Running"),
            "restarting": state.get("Restarting"),
            "oom_killed": state.get("OOMKilled"),
            "exit_code": state.get("ExitCode"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "health": health.get("Status"),
            "failing_streak": health.get("FailingStreak"),
        },
    }


def env_names(raw: Any) -> list[str]:
    """Return environment variable NAMES only. Values are discarded before anything leaves the gate."""
    config = raw.get("Config") if isinstance(raw, dict) and isinstance(raw.get("Config"), dict) else {}
    env = config.get("Env") if isinstance(config.get("Env"), list) else []
    names: list[str] = []
    for item in env:
        key = str(item).split("=", 1)[0]
        if _ENV_KEY.match(key):
            names.append(key)
    return sorted(set(names))


def host_info(info: Any, version: Any) -> dict[str, Any]:
    info = info if isinstance(info, dict) else {}
    version = version if isinstance(version, dict) else {}
    return {
        "hostname": info.get("Name"),
        "server_version": info.get("ServerVersion") or version.get("Version"),
        "api_version": version.get("ApiVersion"),
        "os": info.get("OperatingSystem"),
        "os_type": info.get("OSType"),
        "architecture": info.get("Architecture"),
        "cpus": info.get("NCPU"),
        "memory_bytes": info.get("MemTotal"),
        "containers": info.get("Containers"),
        "containers_running": info.get("ContainersRunning"),
        "containers_stopped": info.get("ContainersStopped"),
    }


def is_healthy(detail: dict[str, Any]) -> bool:
    """Healthy means running AND a defined health check reports healthy. No health check is not proof."""
    state = detail.get("state") or {}
    return bool(state.get("running")) and detail.get("has_healthcheck") is True and state.get("health") == "healthy"
