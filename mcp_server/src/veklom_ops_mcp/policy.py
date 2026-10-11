from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .config import SETTINGS


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
    "docker.exec",
    "docker.create_container",
    "docker.remove_container",
    "docker.read_container_filesystem",
    "docker.socket_access",
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


KNOWN_ACTIONS = FORBIDDEN_ACTIONS | LOW_RISK_ACTIONS | MEDIUM_RISK_ACTIONS | HIGH_RISK_ACTIONS
DEFAULT_MIN_HEALTHY_REPLICAS = 2


class PolicyFileError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyOverlay:
    """Operator policy. It can only tighten the built-in model, never loosen it."""

    forbid: frozenset[str] = frozenset()
    require_approval: frozenset[str] = frozenset()
    min_healthy_replicas: int = DEFAULT_MIN_HEALTHY_REPLICAS

    @classmethod
    def from_dict(cls, data: Any) -> "PolicyOverlay":
        if not isinstance(data, dict):
            raise PolicyFileError("Policy file must be a JSON object.")
        unknown_keys = set(data) - {"forbid", "require_approval", "min_healthy_replicas", "$schema", "description"}
        if unknown_keys:
            raise PolicyFileError(
                f"Unsupported policy keys {sorted(unknown_keys)}. Policy files can only forbid actions, "
                "require approval for medium actions, or raise the redundancy floor."
            )
        forbid = _action_set(data.get("forbid", []), "forbid")
        require_approval = _action_set(data.get("require_approval", []), "require_approval")
        not_medium = require_approval - MEDIUM_RISK_ACTIONS
        if not_medium:
            raise PolicyFileError(
                f"require_approval only applies to medium actions; got {sorted(not_medium)}. "
                "High actions already require approval; use forbid to block any action outright."
            )
        floor = data.get("min_healthy_replicas", DEFAULT_MIN_HEALTHY_REPLICAS)
        if not isinstance(floor, int) or isinstance(floor, bool) or floor < DEFAULT_MIN_HEALTHY_REPLICAS:
            raise PolicyFileError(f"min_healthy_replicas must be an integer >= {DEFAULT_MIN_HEALTHY_REPLICAS}.")
        return cls(forbid=forbid, require_approval=require_approval, min_healthy_replicas=floor)

    @classmethod
    def load(cls, path: Path | None) -> "PolicyOverlay":
        if path is None:
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PolicyFileError(f"Cannot load policy file {path}: {exc}") from exc
        return cls.from_dict(data)


def _action_set(value: Any, key: str) -> frozenset[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyFileError(f"{key} must be a list of action names.")
    unknown = set(value) - KNOWN_ACTIONS
    if unknown:
        raise PolicyFileError(f"{key} names unknown actions {sorted(unknown)}; check spelling against operations_policy.")
    return frozenset(value)


ACTIVE_OVERLAY = PolicyOverlay.load(SETTINGS.policy_file)


def _medium_needs_approval(context: dict[str, Any], min_healthy_replicas: int = DEFAULT_MIN_HEALTHY_REPLICAS) -> tuple[bool, str]:
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
        if not isinstance(healthy_replicas, int) or healthy_replicas < min_healthy_replicas:
            return True, "Production action lacks redundancy proof."
    if context.get("action") == "service.redeploy_same_commit":
        if not same_artifact or not artifact_digest_verified:
            return True, "Redeploy lacks proof that the exact source artifact/commit is unchanged."
    if active_incident and environment == "production":
        return True, "Production incident changes require human/coding-agent approval."

    return False, "Guardrails satisfied; medium-risk action may execute autonomously."


def evaluate(action: str, context: dict[str, Any] | None = None, overlay: PolicyOverlay | None = None) -> PolicyDecision:
    context = dict(context or {})
    context.setdefault("action", action)
    overlay = overlay or ACTIVE_OVERLAY

    if action in FORBIDDEN_ACTIONS:
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.FORBIDDEN,
            allowed=False,
            requires_approval=False,
            reason="Action violates a non-bypassable Veklom trust boundary.",
        )

    if action in overlay.forbid:
        return PolicyDecision(
            action=action,
            risk_tier=RiskTier.FORBIDDEN,
            allowed=False,
            requires_approval=False,
            reason="Action is forbidden by the operator policy file.",
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
        if action in overlay.require_approval:
            requires_approval, reason = True, "Operator policy file requires approval for this action."
        else:
            requires_approval, reason = _medium_needs_approval(context, overlay.min_healthy_replicas)
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
