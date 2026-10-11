from veklom_ops_mcp.safe_projection import container_detail, container_summary, env_names, is_healthy, safe_labels


def test_container_detail_drops_everything_not_allowlisted():
    raw = {
        "Id": "abc",
        "Name": "/web",
        "Config": {"Image": "web:1", "Env": ["SECRET=value"], "Labels": {"com.docker.compose.service": "web", "x-api-key": "k"}, "Cmd": ["--token", "t"]},
        "Mounts": [{"Source": "/etc"}],
        "State": {"Running": True, "Health": {"Status": "healthy", "Log": [{"Output": "secret"}]}},
        "NetworkSettings": {"Networks": {}},
        "future_sensitive_field": "must-not-auto-expose",
    }
    text = str(container_detail(raw))
    for leaked in ("SECRET", "x-api-key", "--token", "/etc", "Log", "future_sensitive_field", "NetworkSettings"):
        assert leaked not in text
    assert container_detail(raw)["name"] == "web"


def test_summary_projection():
    row = {"Id": "abc", "Names": ["/web"], "Labels": {"veklom.ops.tier": "1", "secret.label": "x"}, "Ports": [{"IP": "0.0.0.0"}]}
    summary = container_summary(row)
    assert summary["labels"] == {"veklom.ops.tier": "1"}
    assert "Ports" not in summary and "ports" not in summary


def test_env_names_never_return_values():
    assert env_names({"Config": {"Env": ["A=1", "B=two=2", "=bad", "C"]}}) == ["A", "B", "C"]


def test_safe_labels_ignores_non_dicts():
    assert safe_labels(None) == {}


def test_health_requires_a_defined_passing_healthcheck():
    healthy = {"has_healthcheck": True, "state": {"running": True, "health": "healthy"}}
    assert is_healthy(healthy)
    assert not is_healthy({**healthy, "has_healthcheck": False})
    assert not is_healthy({"has_healthcheck": True, "state": {"running": True, "health": "starting"}})
    assert not is_healthy({"has_healthcheck": True, "state": {"running": False, "health": "healthy"}})
