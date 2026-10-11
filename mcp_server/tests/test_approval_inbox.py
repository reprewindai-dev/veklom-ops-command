"""Approver-device delivery: the inbox and the /approvals/deliver endpoint."""
import base64
import json
from dataclasses import replace

import pytest
from starlette.testclient import TestClient

from veklom_ops_mcp.approval import (
    ApprovalAuthority,
    ApprovalError,
    ApprovalInbox,
    ApprovalSigner,
    build_approval_request,
    generate_keypair,
    params_hash,
    request_id,
)
from veklom_ops_mcp.config import SETTINGS

AUD = "acme-prod"
PARAMS = {"container": "shop-api-1"}


@pytest.fixture()
def keyed(tmp_path):
    public_key, private_key = generate_keypair()
    settings = replace(SETTINGS, approval_public_key_b64=public_key, approval_audience=AUD, approval_store=tmp_path / "approvals.jsonl", approval_ttl_seconds=600)
    authority = ApprovalAuthority(settings)
    return settings, ApprovalInbox(settings, authority), ApprovalSigner(private_key)


def token_for(signer, **overrides):
    args = dict(audience=AUD, tool="stop_container", action="service.stop", params=PARAMS, approved_by="founder")
    args.update(overrides)
    return signer.issue(**args)


def rid():
    return request_id(audience=AUD, tool="stop_container", action="service.stop", params_sha256=params_hash(PARAMS))


def test_delivered_approval_is_held_for_exactly_its_call(keyed):
    _, inbox, signer = keyed
    result = inbox.deliver(token_for(signer))
    assert result["request_id"] == rid()
    assert inbox.status(rid())["state"] == "approved"
    other = request_id(audience=AUD, tool="stop_container", action="service.stop", params_sha256=params_hash({"container": "shop-web-1"}))
    assert inbox.status(other)["state"] == "waiting"
    assert inbox.take(other) is None


def test_take_is_one_shot(keyed):
    _, inbox, signer = keyed
    token = token_for(signer)
    inbox.deliver(token)
    assert inbox.take(rid()) == token
    assert inbox.take(rid()) is None
    assert inbox.status(rid())["state"] == "waiting"


@pytest.mark.parametrize("case", ["wrong_audience", "foreign_key", "garbage", "too_large"])
def test_inbox_refuses_anything_not_signed_for_this_deployment(keyed, case):
    _, inbox, signer = keyed
    if case == "wrong_audience":
        token = token_for(signer, audience="someone-else")
    elif case == "foreign_key":
        token = token_for(ApprovalSigner(generate_keypair()[1]))
    elif case == "garbage":
        token = "v2.not.base64!"
    else:
        token = "v2." + "A" * 5000 + ".x"
    with pytest.raises(ApprovalError):
        inbox.deliver(token)
    assert inbox.status(rid())["state"] == "waiting"


def test_expired_delivery_disappears(keyed, monkeypatch):
    _, inbox, signer = keyed
    inbox.deliver(token_for(signer, ttl_seconds=5))
    real = __import__("time").time
    monkeypatch.setattr("veklom_ops_mcp.approval.time.time", lambda: real() + 60)
    assert inbox.status(rid())["state"] == "waiting"


def test_approval_link_carries_the_exact_call_in_the_fragment():
    request = build_approval_request(
        audience=AUD, tool="stop_container", action="service.stop", params=PARAMS, ttl_seconds=600,
        risk_tier="high", reason="r", approver_url="https://approve.example.com/", deliver_url="https://ops.example.com/approvals/deliver",
    )
    base, fragment = request["approve_url"].split("#r=")
    assert base == "https://approve.example.com/"
    decoded = json.loads(base64.urlsafe_b64decode(fragment + "=" * (-len(fragment) % 4)))
    assert decoded["params"] == PARAMS and decoded["params_sha256"] == params_hash(PARAMS)
    assert decoded["deliver_to"] == "https://ops.example.com/approvals/deliver"
    assert decoded["request_id"] == request["request_id"]


def test_approver_must_not_share_the_mcp_origin():
    settings = replace(SETTINGS, access_token="t", approver_url="https://ops.example.com/approve", public_url="https://ops.example.com")
    with pytest.raises(RuntimeError, match="different origin"):
        settings.validate()


@pytest.fixture()
def http(keyed, monkeypatch):
    from veklom_ops_mcp import main
    from veklom_ops_mcp.audit import AuditLedger

    settings, inbox, signer = keyed
    settings = replace(settings, approver_url="https://approve.example.com/", access_token="inbound", allowed_hosts=[], audit_store=settings.approval_store.with_name("audit.jsonl"))
    monkeypatch.setattr(main, "SETTINGS", settings)
    monkeypatch.setattr(main, "inbox", inbox)
    monkeypatch.setattr(main, "audit", AuditLedger(settings))
    return TestClient(main.app), inbox, signer


def test_deliver_endpoint_accepts_signed_approval_without_bearer(http):
    client, inbox, signer = http
    response = client.post("/approvals/deliver", json={"token": token_for(signer)}, headers={"Origin": "https://approve.example.com"})
    assert response.status_code == 200
    assert response.json()["delivered"] is True
    assert response.headers["access-control-allow-origin"] == "https://approve.example.com"
    assert inbox.status(rid())["state"] == "approved"


def test_deliver_endpoint_rejects_forgeries(http):
    client, inbox, _ = http
    forged = token_for(ApprovalSigner(generate_keypair()[1]))
    response = client.post("/approvals/deliver", json={"token": forged}, headers={"Origin": "https://approve.example.com"})
    assert response.status_code == 400 and response.json()["delivered"] is False
    assert inbox.status(rid())["state"] == "waiting"


def test_deliver_endpoint_refuses_other_browser_origins(http):
    client, _, signer = http
    response = client.post("/approvals/deliver", json={"token": token_for(signer)}, headers={"Origin": "https://evil.example"})
    assert response.status_code == 403


def test_preflight_is_answered_for_the_approver_origin(http):
    client, _, _ = http
    response = client.options("/approvals/deliver", headers={"Origin": "https://approve.example.com", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-methods"] == "POST, OPTIONS"


def test_rest_of_the_server_still_requires_bearer(http):
    client, _, _ = http
    assert client.post("/mcp", json={}).status_code == 401
