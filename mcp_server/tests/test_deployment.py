"""Deployment invariants checked from the shipped files, not from prose."""
import re
from pathlib import Path

import pytest

from veklom_ops_mcp.setup_cli import main as init_main

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILES = ["docker-compose.yml", "deploy/docker-compose.yml"]


def services(compose: str) -> dict[str, str]:
    top = re.split(r"(?m)^(?:networks|volumes):\s*$", compose)[0]
    blocks = re.split(r"(?m)^  ([a-z0-9-]+):\s*$", top)
    return {blocks[i]: blocks[i + 1] for i in range(1, len(blocks), 2)}


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", COMPOSE_FILES)
def test_only_the_gate_mounts_the_docker_socket(name):
    blocks = services(read(name))
    assert set(blocks) == {"veklom-ops-mcp", "docker-gate"}
    assert "docker.sock" in blocks["docker-gate"]
    assert "docker.sock" not in blocks["veklom-ops-mcp"]


@pytest.mark.parametrize("name", COMPOSE_FILES)
def test_nothing_publishes_host_ports_and_gate_has_no_internet_route(name):
    compose = read(name)
    blocks = services(compose)
    for service, block in blocks.items():
        assert "ports:" not in block, f"{service} must not publish host ports"
    assert "- gate" in blocks["docker-gate"] and "- default" not in blocks["docker-gate"]
    assert re.search(r"(?m)^  gate:\n    internal: true", compose)
    # Only the gate decides whether lifecycle actions are possible at all.
    assert "DOCKER_GATE_ALLOW_ACT" in blocks["docker-gate"]
    assert "DOCKER_GATE_ALLOW_ACT" not in blocks["veklom-ops-mcp"]
    assert "env_file" not in blocks["veklom-ops-mcp"], "the MCP must get an explicit variable list"


@pytest.mark.parametrize("name", COMPOSE_FILES)
def test_services_are_hardened(name):
    for service, block in services(read(name)).items():
        assert "read_only: true" in block, service
        assert "- ALL" in block, service
        assert "no-new-privileges:true" in block, service


def test_tunnel_overlay_cannot_reach_the_gate_or_socket():
    block = services(read("deploy/cloudflare-tunnel.yml"))["cloudflared"]
    assert "docker.sock" not in block
    assert "- gate" not in block
    assert re.search(r"cloudflared:\d{4}\.\d+\.\d+", block), "pin the cloudflared version"


def test_no_approval_private_key_in_deployment_files():
    for name in ("docker-compose.yml", ".env.example", "Dockerfile", *COMPOSE_FILES):
        assert "VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64" not in read(name)


def test_no_retired_platform_in_runtime_code():
    # CURRENT_ARCHITECTURE_LOCK.md: Coolify/Hetzner are not part of Core V1.
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "coolify" not in text and "hetzner" not in text, path


def test_init_writes_read_only_env_with_fresh_distinct_secrets(tmp_path):
    out = tmp_path / ".env"
    init_main(["--audience", "acme-prod", "--public-url", "https://ops.example.com", "--approver-url", "https://approve.example.com/", "--socket-gid", "998", "--out", str(out)])
    env = dict(line.split("=", 1) for line in out.read_text().splitlines() if line and not line.startswith("#"))
    assert env["VEKLOM_MCP_WRITES_ENABLED"] == "false" and env["DOCKER_GATE_ALLOW_ACT"] == "false"
    assert env["VEKLOM_MCP_APPROVAL_AUDIENCE"] == "acme-prod"
    assert env["MCP_ALLOWED_HOSTS"] == "ops.example.com"
    assert env["DOCKER_SOCKET_GID"] == "998"
    secrets = [env["VEKLOM_MCP_ACCESS_TOKEN"], env["DOCKER_GATE_READ_TOKEN"], env["DOCKER_GATE_ACT_TOKEN"]]
    assert len(set(secrets)) == 3 and all(len(s) >= 40 for s in secrets)
    assert "PRIVATE_KEY" not in out.read_text()


def test_init_refuses_to_overwrite_and_same_origin_approver(tmp_path):
    out = tmp_path / ".env"
    out.write_text("existing")
    with pytest.raises(SystemExit, match="already exists"):
        init_main(["--audience", "a-b", "--socket-gid", "1", "--out", str(out)])
    with pytest.raises(SystemExit, match="different host"):
        init_main(["--audience", "a-b", "--socket-gid", "1", "--out", str(tmp_path / "x"), "--public-url", "https://ops.example.com", "--approver-url", "https://ops.example.com/approve"])


def test_approver_page_loads_nothing_from_third_parties():
    html = read("approver/index.html")
    assert "script-src 'self'" in html and "default-src 'none'" in html
    assert not re.search(r"<script[^>]+src=\"https?://", html)
    assert not re.search(r"<link[^>]+href=\"https?://", html)
    headers = read("approver/_headers")
    assert "frame-ancestors 'none'" in headers and "X-Frame-Options: DENY" in headers


def test_approver_key_is_generated_non_extractable():
    js = read("approver/app.js")
    assert 'generateKey({ name: "Ed25519" }, false, ["sign", "verify"])' in js
    assert "exportKey(\"raw\", pair.publicKey)" in js and "exportKey(\"pkcs8\"" not in js and "exportKey(\"jwk\"" not in js
