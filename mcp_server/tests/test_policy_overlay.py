import json

import pytest

from veklom_ops_mcp.policy import PolicyFileError, PolicyOverlay, RiskTier, evaluate

REDUNDANT_PROD = {
    "environment": "production",
    "affects_single_instance": True,
    "healthy_replicas": 2,
    "causes_downtime": False,
    "changes_effective_config": False,
    "active_incident": False,
}


def test_empty_overlay_keeps_builtin_behaviour():
    decision = evaluate("service.restart", REDUNDANT_PROD, PolicyOverlay())
    assert decision.requires_approval is False


def test_overlay_can_forbid_a_high_action():
    overlay = PolicyOverlay.from_dict({"forbid": ["service.stop"]})
    decision = evaluate("service.stop", {"environment": "production"}, overlay)
    assert decision.risk_tier is RiskTier.FORBIDDEN
    assert decision.allowed is False


def test_overlay_can_forbid_a_read():
    overlay = PolicyOverlay.from_dict({"forbid": ["infra.logs.read"]})
    assert evaluate("infra.logs.read", {}, overlay).allowed is False


def test_overlay_can_require_approval_for_medium_action():
    overlay = PolicyOverlay.from_dict({"require_approval": ["service.restart"]})
    decision = evaluate("service.restart", REDUNDANT_PROD, overlay)
    assert decision.risk_tier is RiskTier.MEDIUM
    assert decision.requires_approval is True


def test_overlay_can_raise_redundancy_floor():
    overlay = PolicyOverlay.from_dict({"min_healthy_replicas": 3})
    assert evaluate("service.restart", REDUNDANT_PROD, overlay).requires_approval is True


@pytest.mark.parametrize(
    "data, message",
    [
        ({"allow": ["database.write"]}, "Unsupported policy keys"),
        ({"low": ["service.stop"]}, "Unsupported policy keys"),
        ({"min_healthy_replicas": 1}, ">= 2"),
        ({"min_healthy_replicas": True}, ">= 2"),
        ({"require_approval": ["service.stop"]}, "only applies to medium"),
        ({"forbid": ["service.stpo"]}, "unknown actions"),
        ({"forbid": "service.stop"}, "list of action names"),
        (["service.stop"], "JSON object"),
    ],
)
def test_overlay_cannot_loosen_or_be_malformed(data, message):
    with pytest.raises(PolicyFileError, match=message):
        PolicyOverlay.from_dict(data)


def test_builtin_forbidden_floor_survives_any_overlay():
    overlay = PolicyOverlay.from_dict({"forbid": [], "require_approval": []})
    for action in ("database.write", "host.arbitrary_shell", "secret.export", "docker.delete_volume"):
        assert evaluate(action, {"approved": True}, overlay).allowed is False


def test_policy_file_load(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"forbid": ["service.stop"], "min_healthy_replicas": 3}), encoding="utf-8")
    overlay = PolicyOverlay.load(path)
    assert overlay.forbid == {"service.stop"}
    assert overlay.min_healthy_replicas == 3


def test_unreadable_policy_file_fails_closed(tmp_path):
    with pytest.raises(PolicyFileError):
        PolicyOverlay.load(tmp_path / "missing.json")
