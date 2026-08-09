from veklom_ops_mcp.safe_projection import project


def test_application_projection_excludes_unknown_and_sensitive_fields():
    raw = {
        "uuid": "app-1",
        "name": "cappo",
        "git_branch": "main",
        "status": "running",
        "password": "must-not-leak",
        "environment_variables": [{"key": "SECRET", "value": "must-not-leak"}],
        "docker_compose_raw": "services: ...",
        "future_sensitive_field": "must-not-auto-expose",
    }
    result = project("application", raw)
    assert result == {
        "uuid": "app-1",
        "name": "cappo",
        "git_branch": "main",
        "status": "running",
    }


def test_environment_presence_projection_never_returns_values():
    raw = [
        {
            "uuid": "env-1",
            "key": "COVENANT_EVIDENCE_SIGNING_KEY",
            "value": "private-value-must-never-leave",
            "real_value": "decoded-private-value-must-never-leave",
            "is_runtime": True,
            "is_buildtime": False,
            "is_preview": False,
        }
    ]
    result = project("environment_presence", raw)
    assert result == [
        {
            "uuid": "env-1",
            "key": "COVENANT_EVIDENCE_SIGNING_KEY",
            "is_runtime": True,
            "is_buildtime": False,
            "is_preview": False,
        }
    ]
    serialized = repr(result)
    assert "private-value-must-never-leave" not in serialized
    assert "decoded-private-value-must-never-leave" not in serialized


def test_database_projection_never_returns_credentials_or_connection_strings():
    raw = {
        "uuid": "db-1",
        "name": "shared-postgres",
        "type": "postgresql",
        "status": "running",
        "password": "hidden",
        "database_url": "postgres://u:p@db/app",
        "internal_db_url": "postgres://u:p@db/app",
    }
    result = project("database", raw)
    assert result["uuid"] == "db-1"
    assert result["name"] == "shared-postgres"
    assert "password" not in result
    assert "database_url" not in result
    assert "internal_db_url" not in result


def test_list_projection_preserves_only_safe_fields_per_row():
    raw = [
        {"deployment_uuid": "d-1", "status": "queued", "logs": "secret-ish"},
        {"deployment_uuid": "d-2", "status": "finished", "private_key": "no"},
    ]
    result = project("deployment", raw)
    assert result == [
        {"deployment_uuid": "d-1", "status": "queued"},
        {"deployment_uuid": "d-2", "status": "finished"},
    ]
