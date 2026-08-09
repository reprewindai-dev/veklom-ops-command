from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    risk_tier: RiskTier
    allowed: bool
    requires_approval: bool
    reason: str


FORBIDDEN_ACTIONS = {
    "database.write",
    "database.schema_change",
    "database.drop",
    "database.truncate",
    "database.credential_rotate",
    "secret.read_value",
    "secret.export",
    "secret.disable_redaction",
    "airgap.disable",
    "airgap.route_public",
    "zero_trust.disable",
    "zero_trust.bypass",
    "policy.disable_fail_closed",
    "lockerphycer.expose_publicly",
    "docker.delete_volume",
    "docker.system_prune",
    "host.arbitrary_shell",
}

LOW_RISK_ACTIONS = {
    "infra.health.read",
    "infra.topology.read",
    "infra.deployments.read",
    "infra.resources.read",
    "infra.logs.read",
    "infra.routes.read",
    "security.posture.read",
    "security.drift.read",
    "evidence.read",
    "evidence.verify",
    "database.read",
    "database.schema.read",
    "environment.presence.read",
    "github.read",
}

MEDIUM_RISK_ACTIONS = {
    "service.restart",
    "service.redeploy_same_commit",
    "deployment.cancel",
    "proxy.reload",
    "cache.invalidate",
    "runtime.scale_within_bounds",
}

HIGH_RISK_ACTIONS = {
    "service.stop",
    "service.start_after_stop",
    "deployment.change_source_ref",
    "deployment.change_image",
    "deployment.change_build_config",
    "proxy.route_change",
    "environment.change_non_secret",
    "runtime.scale_outside_bounds",
    "host.maintenance_operation",
}


def _medium_needs_approval(context: dict[str, Any]) -> tuple[bool, str]:
    """Resolve conditional approval using proven runtime context only."""
    environment = str(context.get("environment", "production")).lower()
    healthy_replicas = context.get("healthy_replicas")
    affects_single_instance = bool(context.get("affects_single_instance", True))
    causes_downtime = bool(context.get("causes_downtime", False))
    changes_effective_config = bool(context.get("changes_effective_config", False))
    same_artifact = bool(context.get("same_artifact", False))
    artifact_digest_verified = bool(context.get("artifact_digest_verified", False))
    active_incident = bool(context.get("active_incident", False))

    if changes_effective_config:
        return True, "Medium action changes effective configuration."
    if causes_downtime:
        return True, "Medium action may cause user-visible downtime."
    if environment == "production" and affects_single_instance:
        if not isinstance(healthy_replicas, int) or healthy_replicas < 2:
            return True, "Production action lacks redundancy proof."
    if context.get("action") == "service.redeploy_same_commit":
        if not same_artifact or not artifact_digest_verified:
            return True, "Redeploy lacks proof that the exact source artifact/commit is unchanged."
    if active_incident and environment == "production":
        return True, "Production incident changes require human/coding-agent approval."

    return False, "Guardrails satisfied; medium-risk action may execute autonomously."


def evaluate(action: str, context: dict[str, Any] | None = None) -> PolicyDecision:
    context = dict(context or {})
    context.setdefault("action", action)

    if action in FORBIDDEN_ACTIONS:
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.FORBIDDEN,
            allowed=False,
            requires_approval=False,
            reason="Action violates a non-bypassable Veklom trust boundary.",
        )

    if action in LOW_RISK_ACTIONS:
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.LOW,
            allowed=True,
            requires_approval=False,
            reason="Low-risk action is authorized for autonomous execution.",
        )

    if action in MEDIUM_RISK_ACTIONS:
        requires_approval, reason = _medium_needs_approval(context)
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.MEDIUM,
            allowed=True,
            requires_approval=requires_approval,
            reason=reason,
        )

    if action in HIGH_RISK_ACTIONS:
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.HIGH,
            allowed=True,
            requires_approval=True,
            reason="High-risk production or configuration action requires explicit approval.",
        )

    return PolicyDecision(
        action=action,
        risk_tier=RiskTier.HIGH,
        allowed=False,
        requires_approval=True,
        reason="Unknown action fails closed until it is explicitly classified.",
    )
