from __future__ import annotations

from typing import Any

SAFE_FIELDS: dict[str, set[str]] = {
    "server": {
        "uuid", "name", "description", "ip", "port", "proxy_type", "proxy_status",
        "is_reachable", "is_usable", "created_at", "updated_at", "timezone",
    },
    "application": {
        "id", "uuid", "name", "description", "fqdn", "config_hash", "git_repository",
        "git_branch", "git_commit_sha", "git_full_url", "docker_registry_image_name",
        "docker_registry_image_tag", "build_pack", "ports_exposes", "health_check_enabled",
        "health_check_path", "health_check_port", "health_check_method", "status",
        "environment_id", "destination_id", "swarm_replicas", "created_at", "updated_at",
    },
    "database": {
        "id", "uuid", "name", "description", "type", "status", "image", "is_public",
        "public_port", "environment_id", "destination_id", "created_at", "updated_at",
    },
    "service": {
        "id", "uuid", "name", "description", "status", "server_status", "environment_id",
        "destination_id", "created_at", "updated_at",
    },
    "deployment": {
        "id", "application_id", "deployment_uuid", "pull_request_id", "force_rebuild",
        "commit", "status", "is_webhook", "is_api", "created_at", "updated_at",
        "restart_only", "git_type", "server_id", "application_name", "server_name",
        "deployment_url", "destination_id", "only_this_server", "rollback",
    },
    "backup": {
        "id", "uuid", "database_id", "database_uuid", "frequency", "enabled", "status",
        "last_run", "last_run_at", "created_at", "updated_at", "number_of_backups_locally",
        "save_s3", "s3_storage_id",
    },
}


def _project_row(kind: str, row: Any) -> Any:
    if not isinstance(row, dict):
        return row
    allowed = SAFE_FIELDS[kind]
    return {key: row[key] for key in allowed if key in row}


def project(kind: str, value: Any) -> Any:
    """Return an allowlisted operational view instead of trusting upstream omission/redaction."""
    if kind not in SAFE_FIELDS:
        raise ValueError(f"Unknown safe projection kind: {kind}")
    if isinstance(value, list):
        return [_project_row(kind, row) for row in value]
    if isinstance(value, dict) and isinstance(value.get("data"), list):
        result = {"data": [_project_row(kind, row) for row in value["data"]]}
        if isinstance(value.get("_pagination"), dict):
            result["_pagination"] = value["_pagination"]
        return result
    return _project_row(kind, value)
