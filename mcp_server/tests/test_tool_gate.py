"""End to end: MCP tool -> policy -> approval -> Docker gate (real app) -> fake Docker Engine -> audit."""
import asyncio
from dataclasses import replace

import httpx
import pytest

from fake_docker import FakeDocker, container
from veklom_ops_mcp import tools
from veklom_ops_mcp.approval import ApprovalAuthority, ApprovalSigner, generate_keypair
from veklom_ops_mcp.audit import AuditLedger
from veklom_ops_mcp.clients import DockerGateClient
from veklom_ops_mcp.config import SETTINGS
from veklom_ops_mcp.docker_gate import GateSettings, build_app

AUD = "acme-prod"
WEB1, WEB2, API1 = "1" * 64, "2" * 64, "3" * 64


@pytest.fixture()
def stack(tmp_path, monkeypatch):
    fake = FakeDocker([
        container(WEB1, "shop-web-1", service="web"),
        container(WEB2, "shop-web-2", service="web"),
        container(API1, "shop-api-1", service="api"),
        container("4" * 64, "shop-db-1", service="db", managed=False),
    ])
    gate = build_app(
        GateSettings(socket_path="/nonexistent", read_token="gate-read", act_token="gate-act", allow_act=True, managed_label="veklom.ops.managed=true", stop_timeout_seconds=10),
        fake.transport,
    )
    public_key, private_key = generate_keypair()
    settings = replace(
        SETTINGS,
        environment="production",
        writes_enabled=True,
        docker_gate_url="http://gate",
        docker_gate_read_token="gate-read",
        docker_gate_act_token="gate-act",
        approval_public_key_b64=public_key,
        approval_audience=AUD,
        approval_store=tmp_path / "approvals.jsonl",
        audit_store=tmp_path / "audit.jsonl",
        audit_anchor_url=None,
    )
    monkeypatch.setattr(tools, "SETTINGS", settings)
    monkeypatch.setattr(tools, "approvals", ApprovalAuthority(settings))
    monkeypatch.setattr(tools, "audit", AuditLedger(settings))
    monkeypatch.setattr(tools, "docker", DockerGateClient(settings, transport=httpx.ASGITransport(app=gate)))
    return fake, ApprovalSigner(private_key)


def run(coro):
    return asyncio.run(coro)


def posts(fake):
    return [path for method, path in fake.requests if method == "POST"]


def approve(signer, tool, container, action):
    return signer.issue(audience=AUD, tool=tool, action=action, params={"container": container}, approved_by="founder")


def test_restart_with_healthy_sibling_runs_autonomously(stack):
    fake, _ = stack
    result = run(tools.restart_container("shop-web-1"))
    assert result["status"] == "executed"
    assert posts(fake) == [f"/containers/{WEB1}/restart"]


def test_restart_of_single_replica_service_needs_approval(stack):
    fake, _ = stack
    result = run(tools.restart_container("shop-api-1"))
    assert result["status"] == "approval_required"
    assert posts(fake) == []


def test_restart_counts_only_observed_healthy_replicas(stack):
    fake, _ = stack
    fake.containers[WEB2]["State"]["Health"]["Status"] = "unhealthy"
    assert run(tools.restart_container("shop-web-1"))["status"] == "approval_required"
    assert posts(fake) == []


def test_replicas_without_healthchecks_are_not_proof(stack):
    fake, _ = stack
    for cid in (WEB1, WEB2):
        fake.containers[cid]["Config"]["Healthcheck"] = {"Test": ["NONE"]}
        fake.containers[cid]["State"]["Health"] = None
    assert run(tools.restart_container("shop-web-1"))["status"] == "approval_required"


def test_stop_needs_approval_then_runs_once(stack):
    fake, signer = stack
    request = run(tools.stop_container("shop-web-1"))
    assert request["status"] == "approval_required"
    assert request["approval_request"]["params"] == {"container": "shop-web-1"}
    token = approve(signer, "stop_container", "shop-web-1", "service.stop")
    assert run(tools.stop_container("shop-web-1", approval_token=token))["status"] == "executed"
    assert run(tools.stop_container("shop-web-1", approval_token=token))["status"] == "approval_rejected"
    assert posts(fake) == [f"/containers/{WEB1}/stop"]


def test_approval_for_one_container_cannot_stop_another(stack):
    fake, signer = stack
    token = approve(signer, "stop_container", "shop-web-1", "service.stop")
    assert run(tools.stop_container("shop-web-2", approval_token=token))["status"] == "approval_rejected"
    assert posts(fake) == []


def test_approved_stop_of_unmanaged_container_still_cannot_happen(stack):
    fake, signer = stack
    token = approve(signer, "stop_container", "shop-db-1", "service.stop")
    result = run(tools.stop_container("shop-db-1", approval_token=token))
    assert result["status"] == "upstream_error"
    assert result["approval_consumed"] is True
    assert posts(fake) == []


def test_reads_never_leak_env_values(stack):
    detail = run(tools.get_container("shop-web-1"))
    names = run(tools.get_container_env_presence("shop-web-1"))
    logs = run(tools.get_container_logs("shop-web-1", lines=50))
    text = str(detail) + str(names) + str(logs)
    assert "s3cr3t" not in text and "hunter2" not in text
    assert names["env_names"] == ["DATABASE_URL", "PORT"]


def test_unmanaged_containers_are_invisible(stack):
    names = [row["name"] for row in run(tools.list_containers())]
    assert "shop-db-1" not in names and len(names) == 3


def test_every_decision_is_audited(stack):
    _, signer = stack
    run(tools.stop_container("shop-web-1"))
    run(tools.stop_container("shop-web-1", approval_token=approve(signer, "stop_container", "shop-web-1", "service.stop")))
    events = tools.audit.tail(10)
    assert [e["outcome"] for e in events] == ["approval_required", "success"]
    assert events[-1]["approved_by"] == "founder"
    assert tools.audit.verify()["valid"] is True
