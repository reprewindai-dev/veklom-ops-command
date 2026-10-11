import argparse
import base64
import json
from dataclasses import replace

import pytest

from veklom_ops_mcp.approval import (
    ApprovalAuthority,
    ApprovalError,
    ApprovalSigner,
    build_approval_request,
    generate_keypair,
    resolve_request,
)
from veklom_ops_mcp.config import SETTINGS

AUD = "acme-prod"
PARAMS = {"application_uuid": "app-123"}


def authority_pair(tmp_path, audience=AUD, store="approvals.jsonl"):
    public_key, private_key = generate_keypair()
    settings = replace(
        SETTINGS,
        approval_public_key_b64=public_key,
        approval_audience=audience,
        approval_store=tmp_path / store,
        approval_ttl_seconds=600,
    )
    return ApprovalAuthority(settings), ApprovalSigner(private_key, max_ttl_seconds=600), public_key, private_key


def issue(signer, *, audience=AUD, tool="stop_application", action="service.stop", params=PARAMS, ttl=None):
    return signer.issue(audience=audience, tool=tool, action=action, params=params, approved_by="founder:test", ttl_seconds=ttl)


def consume(authority, token, *, tool="stop_application", action="service.stop", params=PARAMS):
    return authority.verify_and_consume(token, tool=tool, action=action, params=params)


def test_server_authority_is_verify_only(tmp_path):
    authority, *_ = authority_pair(tmp_path)
    assert not hasattr(authority, "issue")
    assert not hasattr(authority, "private_key")


def test_approval_is_bound_to_exact_call(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    claims = consume(authority, issue(signer))
    assert claims.approved_by == "founder:test"
    assert claims.aud == AUD


def test_approval_rejects_parameter_substitution(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    with pytest.raises(ApprovalError, match="different parameters"):
        consume(authority, issue(signer), params={"application_uuid": "app-999"})


def test_approval_rejects_action_substitution(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    with pytest.raises(ApprovalError, match="different action"):
        consume(authority, issue(signer), action="service.start_after_stop")


def test_approval_rejects_tool_substitution(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    with pytest.raises(ApprovalError, match="different tool"):
        consume(authority, issue(signer), tool="stop_service")


def test_approval_is_single_use(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    token = issue(signer)
    consume(authority, token)
    with pytest.raises(ApprovalError, match="already been consumed"):
        consume(authority, token)


def test_approval_cannot_be_replayed_on_another_deployment_sharing_the_key(tmp_path):
    staging, signer, public_key, _ = authority_pair(tmp_path, audience="acme-staging", store="staging.jsonl")
    production = ApprovalAuthority(replace(staging.settings, approval_audience="acme-prod", approval_store=tmp_path / "prod.jsonl"))
    token = issue(signer, audience="acme-staging")
    consume(staging, token)
    with pytest.raises(ApprovalError, match="different deployment"):
        consume(production, token)


def test_unconfigured_audience_fails_closed(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path, audience=None)
    with pytest.raises(ApprovalError, match="audience is not configured"):
        consume(authority, issue(signer))


def test_legacy_v1_tokens_are_rejected(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    token = issue(signer)
    with pytest.raises(ApprovalError, match="Unsupported approval token version"):
        consume(authority, "v1." + token.split(".", 1)[1])


def test_tampered_signature_is_rejected(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    token = issue(signer)
    token = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ApprovalError, match="signature"):
        consume(authority, token)


def test_tampered_claims_are_rejected(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    version, payload_b64, sig = issue(signer).split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))
    claims["aud"] = "attacker-chosen"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    with pytest.raises(ApprovalError, match="signature"):
        consume(authority, f"{version}.{forged}.{sig}")


def test_token_signed_by_untrusted_key_is_rejected(tmp_path):
    authority, *_ = authority_pair(tmp_path)
    _, other_private = generate_keypair()
    with pytest.raises(ApprovalError, match="signature"):
        consume(authority, issue(ApprovalSigner(other_private)))


def test_token_ttl_cannot_exceed_server_policy(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    strict = ApprovalAuthority(replace(authority.settings, approval_ttl_seconds=60))
    with pytest.raises(ApprovalError, match="TTL exceeds"):
        consume(strict, issue(signer, ttl=120))


def _cli_args(**overrides):
    base = dict(request_json=None, tool=None, action=None, params_json=None, audience=None)
    base.update(overrides)
    return argparse.Namespace(**base)


def test_approver_signs_exactly_the_relayed_request(tmp_path):
    authority, signer, *_ = authority_pair(tmp_path)
    request = build_approval_request(audience=AUD, tool="stop_application", action="service.stop", params=PARAMS, ttl_seconds=600)
    audience, tool, action, params = resolve_request(_cli_args(request_json=json.dumps({"approval_request": request})), [AUD])
    token = signer.issue(audience=audience, tool=tool, action=action, params=params, approved_by="founder:test")
    assert consume(authority, token).tool == "stop_application"


def test_approver_refuses_request_whose_hash_does_not_match_params(tmp_path):
    request = build_approval_request(audience=AUD, tool="stop_application", action="service.stop", params=PARAMS, ttl_seconds=600)
    request["params"] = {"application_uuid": "app-999"}
    with pytest.raises(ApprovalError, match="does not match"):
        resolve_request(_cli_args(request_json=json.dumps(request)), [AUD])


def test_approver_refuses_unpinned_audience(tmp_path):
    request = build_approval_request(audience="someone-elses-prod", tool="stop_application", action="service.stop", params=PARAMS, ttl_seconds=600)
    with pytest.raises(ApprovalError, match="not in VEKLOM_MCP_APPROVER_AUDIENCES"):
        resolve_request(_cli_args(request_json=json.dumps(request)), [AUD])
