from dataclasses import replace

import pytest

from veklom_ops_mcp.approval import ApprovalAuthority, ApprovalError
from veklom_ops_mcp.config import SETTINGS


def authority(tmp_path):
    settings = replace(
        SETTINGS,
        approval_hmac_key="test-approval-key-that-is-not-production",
        approval_store=tmp_path / "approvals.jsonl",
        approval_ttl_seconds=600,
    )
    return ApprovalAuthority(settings)


def test_approval_is_bound_to_exact_action_and_params(tmp_path):
    auth = authority(tmp_path)
    params = {"application_uuid": "app-123"}
    token = auth.issue("service.stop", params, "founder:test")
    claims = auth.verify_and_consume(token, "service.stop", params)
    assert claims.approved_by == "founder:test"


def test_approval_rejects_parameter_substitution(tmp_path):
    auth = authority(tmp_path)
    token = auth.issue("service.stop", {"application_uuid": "app-123"}, "founder:test")
    with pytest.raises(ApprovalError, match="different parameters"):
        auth.verify_and_consume(token, "service.stop", {"application_uuid": "app-999"})


def test_approval_rejects_action_substitution(tmp_path):
    auth = authority(tmp_path)
    params = {"application_uuid": "app-123"}
    token = auth.issue("service.stop", params, "founder:test")
    with pytest.raises(ApprovalError, match="different action"):
        auth.verify_and_consume(token, "service.start_after_stop", params)


def test_approval_is_single_use(tmp_path):
    auth = authority(tmp_path)
    params = {"application_uuid": "app-123"}
    token = auth.issue("service.stop", params, "founder:test")
    auth.verify_and_consume(token, "service.stop", params)
    with pytest.raises(ApprovalError, match="already been consumed"):
        auth.verify_and_consume(token, "service.stop", params)


def test_tampered_signature_is_rejected(tmp_path):
    auth = authority(tmp_path)
    params = {"application_uuid": "app-123"}
    token = auth.issue("service.stop", params, "founder:test")
    token = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ApprovalError, match="signature"):
        auth.verify_and_consume(token, "service.stop", params)
