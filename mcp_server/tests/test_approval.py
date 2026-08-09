from dataclasses import replace

import pytest

from veklom_ops_mcp.approval import ApprovalAuthority, ApprovalError, ApprovalSigner, generate_keypair
from veklom_ops_mcp.config import SETTINGS


def authority_pair(tmp_path):
    public_key, private_key = generate_keypair()
    settings = replace(
        SETTINGS,
        approval_public_key_b64=public_key,
        approval_store=tmp_path / "approvals.jsonl",
        approval_ttl_seconds=600,
    )
    return ApprovalAuthority(settings), ApprovalSigner(private_key, max_ttl_seconds=600)


def test_server_authority_is_verify_only(tmp_path):
    authority, _ = authority_pair(tmp_path)
    assert not hasattr(authority, "issue")
    assert not hasattr(authority, "private_key")


def test_approval_is_bound_to_exact_action_and_params(tmp_path):
    authority, signer = authority_pair(tmp_path)
    params = {"application_uuid": "app-123"}
    token = signer.issue("service.stop", params, "founder:test")
    claims = authority.verify_and_consume(token, "service.stop", params)
    assert claims.approved_by == "founder:test"


def test_approval_rejects_parameter_substitution(tmp_path):
    authority, signer = authority_pair(tmp_path)
    token = signer.issue("service.stop", {"application_uuid": "app-123"}, "founder:test")
    with pytest.raises(ApprovalError, match="different parameters"):
        authority.verify_and_consume(token, "service.stop", {"application_uuid": "app-999"})


def test_approval_rejects_action_substitution(tmp_path):
    authority, signer = authority_pair(tmp_path)
    params = {"application_uuid": "app-123"}
    token = signer.issue("service.stop", params, "founder:test")
    with pytest.raises(ApprovalError, match="different action"):
        authority.verify_and_consume(token, "service.start_after_stop", params)


def test_approval_is_single_use(tmp_path):
    authority, signer = authority_pair(tmp_path)
    params = {"application_uuid": "app-123"}
    token = signer.issue("service.stop", params, "founder:test")
    authority.verify_and_consume(token, "service.stop", params)
    with pytest.raises(ApprovalError, match="already been consumed"):
        authority.verify_and_consume(token, "service.stop", params)


def test_tampered_signature_is_rejected(tmp_path):
    authority, signer = authority_pair(tmp_path)
    params = {"application_uuid": "app-123"}
    token = signer.issue("service.stop", params, "founder:test")
    token = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ApprovalError, match="signature"):
        authority.verify_and_consume(token, "service.stop", params)


def test_token_signed_by_untrusted_key_is_rejected(tmp_path):
    authority, _ = authority_pair(tmp_path)
    _, other_private = generate_keypair()
    attacker = ApprovalSigner(other_private, max_ttl_seconds=600)
    token = attacker.issue("service.stop", {"application_uuid": "app-123"}, "not-trusted")
    with pytest.raises(ApprovalError, match="signature"):
        authority.verify_and_consume(token, "service.stop", {"application_uuid": "app-123"})


def test_token_ttl_cannot_exceed_server_policy(tmp_path):
    public_key, private_key = generate_keypair()
    settings = replace(
        SETTINGS,
        approval_public_key_b64=public_key,
        approval_store=tmp_path / "approvals.jsonl",
        approval_ttl_seconds=60,
    )
    authority = ApprovalAuthority(settings)
    signer = ApprovalSigner(private_key, max_ttl_seconds=600)
    token = signer.issue("service.stop", {"application_uuid": "app-123"}, "founder:test", ttl_seconds=120)
    with pytest.raises(ApprovalError, match="TTL exceeds"):
        authority.verify_and_consume(token, "service.stop", {"application_uuid": "app-123"})
