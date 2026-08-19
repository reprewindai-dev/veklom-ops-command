from veklom_ops_mcp.policy import RiskTier, evaluate


def test_low_risk_is_autonomous():
    decision = evaluate("infra.health.read", {"environment": "production"})
    assert decision.allowed is True
    assert decision.risk_tier is RiskTier.LOW
    assert decision.requires_approval is False


def test_medium_prod_single_instance_escalates():
    decision = evaluate(
        "service.restart",
        {
            "environment": "production",
            "affects_single_instance": True,
            "healthy_replicas": 1,
            "causes_downtime": False,
            "changes_effective_config": False,
        },
    )
    assert decision.allowed is True
    assert decision.risk_tier is RiskTier.MEDIUM
    assert decision.requires_approval is True


def test_medium_redundant_safe_operation_can_be_autonomous():
    decision = evaluate(
        "service.restart",
        {
            "environment": "production",
            "affects_single_instance": True,
            "healthy_replicas": 3,
            "causes_downtime": False,
            "changes_effective_config": False,
            "active_incident": False,
        },
    )
    assert decision.allowed is True
    assert decision.risk_tier is RiskTier.MEDIUM
    assert decision.requires_approval is False


def test_medium_config_change_escalates():
    decision = evaluate(
        "proxy.reload",
        {
            "environment": "sandbox",
            "affects_single_instance": False,
            "healthy_replicas": 2,
            "causes_downtime": False,
            "changes_effective_config": True,
        },
    )
    assert decision.requires_approval is True


def test_redeploy_same_branch_without_artifact_digest_still_escalates():
    decision = evaluate(
        "service.redeploy_same_commit",
        {
            "environment": "sandbox",
            "affects_single_instance": False,
            "healthy_replicas": 2,
            "causes_downtime": False,
            "changes_effective_config": False,
            "same_artifact": True,
            "artifact_digest_verified": False,
        },
    )
    assert decision.risk_tier is RiskTier.MEDIUM
    assert decision.requires_approval is True
    assert "exact source artifact" in decision.reason


def test_redeploy_can_be_autonomous_only_when_exact_artifact_is_verified():
    decision = evaluate(
        "service.redeploy_same_commit",
        {
            "environment": "sandbox",
            "affects_single_instance": False,
            "healthy_replicas": 2,
            "causes_downtime": False,
            "changes_effective_config": False,
            "same_artifact": True,
            "artifact_digest_verified": True,
            "active_incident": False,
        },
    )
    assert decision.allowed is True
    assert decision.risk_tier is RiskTier.MEDIUM
    assert decision.requires_approval is False


def test_high_always_needs_approval():
    decision = evaluate("service.stop", {"environment": "sandbox"})
    assert decision.allowed is True
    assert decision.risk_tier is RiskTier.HIGH
    assert decision.requires_approval is True


def test_database_write_is_non_bypassably_forbidden():
    decision = evaluate("database.write", {"environment": "sandbox", "approved": True})
    assert decision.allowed is False
    assert decision.risk_tier is RiskTier.FORBIDDEN
    assert decision.requires_approval is False


def test_zero_trust_bypass_is_non_bypassably_forbidden():
    decision = evaluate("zero_trust.bypass", {"environment": "production", "approved": True})
    assert decision.allowed is False
    assert decision.risk_tier is RiskTier.FORBIDDEN


def test_airgap_route_public_is_non_bypassably_forbidden():
    decision = evaluate("airgap.route_public", {"environment": "production", "approved": True})
    assert decision.allowed is False
    assert decision.risk_tier is RiskTier.FORBIDDEN


def test_unknown_action_fails_closed():
    decision = evaluate("made.up.action", {"environment": "sandbox"})
    assert decision.allowed is False
    assert decision.risk_tier is RiskTier.HIGH
    assert decision.requires_approval is True
