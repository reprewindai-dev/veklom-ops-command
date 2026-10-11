"""Deployment invariants checked from the shipped files, not from prose."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def services(compose: str) -> dict[str, str]:
    top = re.split(r"(?m)^(?:networks|volumes):\s*$", compose)[0]
    blocks = re.split(r"(?m)^  ([a-z0-9-]+):\s*$", top)
    return {blocks[i]: blocks[i + 1] for i in range(1, len(blocks), 2)}


def test_only_the_gate_mounts_the_docker_socket():
    blocks = services((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert set(blocks) == {"veklom-ops-mcp", "docker-gate"}
    assert "docker.sock" in blocks["docker-gate"]
    assert "docker.sock" not in blocks["veklom-ops-mcp"]


def test_nothing_publishes_host_ports_and_gate_has_no_internet_route():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    blocks = services(compose)
    for name, block in blocks.items():
        assert "ports:" not in block, f"{name} must not publish host ports"
    assert "- gate" in blocks["docker-gate"] and "- default" not in blocks["docker-gate"]
    assert re.search(r"(?m)^  gate:\n    internal: true", compose)
    # Only the gate decides whether lifecycle actions are possible at all.
    assert "DOCKER_GATE_ALLOW_ACT" in blocks["docker-gate"]
    assert "DOCKER_GATE_ALLOW_ACT" not in blocks["veklom-ops-mcp"]


def test_both_services_are_hardened():
    blocks = services((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    for name, block in blocks.items():
        assert "read_only: true" in block, name
        assert "- ALL" in block, name
        assert "no-new-privileges:true" in block, name


def test_no_approval_private_key_in_deployment_files():
    for name in ("docker-compose.yml", ".env.example", "Dockerfile"):
        assert "VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64" not in (ROOT / name).read_text(encoding="utf-8")


def test_no_retired_platform_in_runtime_code():
    # CURRENT_ARCHITECTURE_LOCK.md: Coolify/Hetzner are not part of Core V1.
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "coolify" not in text and "hetzner" not in text, path
