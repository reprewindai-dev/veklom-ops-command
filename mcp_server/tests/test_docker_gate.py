import pytest
from starlette.testclient import TestClient

from fake_docker import FakeDocker, container
from veklom_ops_mcp.docker_gate import GateSettings, build_app, demux_log_stream

READ = {"Authorization": "Bearer read-token"}
ACT = {"Authorization": "Bearer act-token"}
WEB1 = "1" * 64


def settings(**overrides):
    base = dict(socket_path="/nonexistent", read_token="read-token", act_token="act-token", allow_act=True, managed_label="veklom.ops.managed=true", stop_timeout_seconds=10)
    base.update(overrides)
    return GateSettings(**base)


@pytest.fixture()
def fake():
    return FakeDocker([
        container(WEB1, "shop-web-1"),
        container("2" * 64, "shop-db-1", service="db", managed=False),
    ])


def client(fake, **overrides):
    return TestClient(build_app(settings(**overrides), fake.transport))


def test_health_is_public_and_minimal(fake):
    assert client(fake).get("/health").json() == {"status": "ok", "service": "veklom-docker-gate"}


def test_reads_require_read_token(fake):
    c = client(fake)
    assert c.get("/v1/containers").status_code == 401
    assert c.get("/v1/containers", headers=ACT).status_code == 401
    assert c.get("/v1/containers", headers=READ).status_code == 200


def test_actions_require_act_token(fake):
    c = client(fake)
    assert c.post(f"/v1/containers/{WEB1}/restart", headers=READ).status_code == 401
    assert c.post(f"/v1/containers/{WEB1}/restart", headers=ACT).status_code == 200


def test_actions_are_off_unless_enabled(fake):
    c = client(fake, allow_act=False)
    response = c.post(f"/v1/containers/{WEB1}/restart", headers=ACT)
    assert response.status_code == 403
    assert ("POST", f"/containers/{WEB1}/restart") not in fake.requests


def test_only_managed_containers_are_listed(fake):
    rows = client(fake).get("/v1/containers", headers=READ).json()
    assert [row["name"] for row in rows] == ["shop-web-1"]


def test_unmanaged_container_looks_missing_for_read_and_act(fake):
    c = client(fake)
    assert c.get("/v1/containers/shop-db-1", headers=READ).status_code == 404
    assert c.post("/v1/containers/shop-db-1/stop", headers=ACT).status_code == 404
    assert not any(method == "POST" for method, _ in fake.requests)


def test_inspect_never_returns_env_mounts_args_or_healthcheck_output(fake):
    body = client(fake).get("/v1/containers/shop-web-1", headers=READ).text
    for leaked in ("s3cr3t", "DATABASE_URL", "hunter2", "/srv/secrets", "token=abc123", "Privileged"):
        assert leaked not in body


def test_labels_are_allowlisted(fake):
    fake.containers[WEB1]["Config"]["Labels"]["traefik.http.middlewares.auth.basicauth.users"] = "admin:$apr1$hash"
    detail = client(fake).get("/v1/containers/shop-web-1", headers=READ).json()
    assert "traefik.http.middlewares.auth.basicauth.users" not in detail["labels"]
    assert detail["labels"]["com.docker.compose.service"] == "web"


def test_env_names_without_values(fake):
    body = client(fake).get("/v1/containers/shop-web-1/env-names", headers=READ).json()
    assert body["env_names"] == ["DATABASE_URL", "PORT"]
    assert "s3cr3t" not in str(body)


def test_logs_are_demuxed_capped_and_redacted(fake):
    body = client(fake).get("/v1/containers/shop-web-1/logs?tail=99999", headers=READ).json()
    assert body["lines"] == 500
    assert "started on :8080" in body["logs"]
    assert "hunter2" not in body["logs"]
    assert "\x01\x00\x00\x00" not in body["logs"]


@pytest.mark.parametrize("ref", ["..", "shop-web-1%2F..%2F..%2Fimages", "-rf", "a" * 200, "x;rm"])
def test_hostile_container_references_never_reach_docker(fake, ref):
    c = client(fake)
    response = c.get(f"/v1/containers/{ref}", headers=READ)
    assert response.status_code in {400, 404}
    assert fake.requests == []


def test_lifecycle_uses_resolved_full_id(fake):
    client(fake).post("/v1/containers/shop-web-1/stop", headers=ACT)
    assert ("POST", f"/containers/{WEB1}/stop") in fake.requests


@pytest.mark.parametrize("path", ["/v1/containers/shop-web-1/exec", "/v1/containers/create", "/v1/volumes", "/v1/images", "/v1/containers/shop-web-1/archive"])
def test_no_route_exists_for_dangerous_operations(fake, path):
    c = client(fake)
    assert c.post(path, headers=ACT).status_code in {404, 405}
    assert c.get(path, headers=READ).status_code in {404, 405}


def test_host_info_is_projected(fake):
    body = client(fake).get("/v1/host", headers=READ).json()
    assert body["server_version"] == "27.3.1"
    assert "RegistryConfig" not in str(body)


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"read_token": None}, "READ_TOKEN"),
        ({"act_token": None}, "ACT_TOKEN"),
        ({"act_token": "read-token"}, "different"),
        ({"managed_label": "nolabel"}, "key=value"),
    ],
)
def test_gate_refuses_unsafe_configuration(overrides, message):
    with pytest.raises(RuntimeError, match=message):
        settings(**overrides).validate()


def test_demux_passes_through_raw_tty_output():
    assert demux_log_stream(b"plain text log line\n") == b"plain text log line\n"
