from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .approval import ApprovalAuthority, ApprovalError, ApprovalInbox, build_approval_request, params_hash, request_id
from .audit import AuditLedger
from .clients import DockerGateClient, UpstreamError, VeklomClient
from .config import SETTINGS
from . import policy as policy_module
from .policy import (
    FORBIDDEN_ACTIONS,
    HIGH_RISK_ACTIONS,
    LOW_RISK_ACTIONS,
    MEDIUM_RISK_ACTIONS,
    PolicyDecision,
    evaluate,
)
from .redaction import redact

def transport_security(allowed_hosts: list[str], allowed_origins: list[str]) -> TransportSecuritySettings:
    """Mirror MCP_ALLOWED_HOSTS/ORIGINS into the SDK's DNS-rebinding guard.

    Left unset, the SDK only accepts localhost Host headers, so every tunnelled or service-name
    deployment fails with 421. With no hosts configured, InboundSecurityMiddleware's bearer check
    remains the boundary; production should set MCP_ALLOWED_HOSTS.
    """
    if not allowed_hosts:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[form for host in allowed_hosts for form in (host, f"{host}:*")],
        allowed_origins=allowed_origins or [f"https://{host}" for host in allowed_hosts],
    )


mcp = FastMCP(
    SETTINGS.service_name,
    transport_security=transport_security(SETTINGS.allowed_hosts, SETTINGS.allowed_origins),
    instructions=(
        "Veklom governed operations plane. Read tools are least-authority. "
        "State-changing tools are risk-classified, approval-gated when required, "
        "and every call is hash-chain audited. Never request or reveal secret values."
    ),
    stateless_http=True,
    json_response=True,
)

docker = DockerGateClient()
veklom = VeklomClient()
audit = AuditLedger()
approvals = ApprovalAuthority()
inbox = ApprovalInbox(authority=approvals)


def _decision_dict(decision: PolicyDecision) -> dict[str, Any]:
    return {
        "action": decision.action,
        "risk_tier": decision.risk_tier.value,
        "allowed": decision.allowed,
        "requires_approval": decision.requires_approval,
        "reason": decision.reason,
    }


async def _read_call(
    *,
    tool: str,
    action: str,
    params: dict[str, Any],
    operation: Callable[[], Awaitable[Any]],
) -> Any:
    decision = evaluate(action, {"environment": SETTINGS.environment})
    if not decision.allowed:
        result = {"status": "denied", "policy": _decision_dict(decision)}
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="denied", request=params, result=result, reason=decision.reason)
        return result
    try:
        result = redact(await operation(), max_chars=SETTINGS.max_response_chars)
    except UpstreamError as exc:
        result = {"status": "upstream_error", "error": str(exc)}
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="error", request=params, result=result, reason=str(exc))
        return result
    audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="success", request=params, result=result)
    return result


async def _write_call(
    *,
    tool: str,
    action: str,
    params: dict[str, Any],
    context: dict[str, Any],
    approval_token: str | None,
    operation: Callable[[], Awaitable[Any]],
) -> Any:
    decision = evaluate(action, context)
    policy = _decision_dict(decision)
    if not decision.allowed:
        result = {"status": "denied", "policy": policy}
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="denied", request=params, result=result, reason=decision.reason)
        return result
    if not SETTINGS.writes_enabled:
        result = {"status": "write_plane_disabled", "policy": policy}
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="denied", request=params, result=result, reason="Write plane disabled by deployment configuration.")
        return result

    approved_by: str | None = None
    if decision.requires_approval:
        if not approval_token:
            # An approver device may already have delivered a signed approval for exactly this call.
            rid = request_id(audience=SETTINGS.approval_audience or "", tool=tool, action=action, params_sha256=params_hash(params))
            approval_token = inbox.take(rid)
        if not approval_token:
            result = {
                "status": "approval_required",
                "policy": policy,
                "approval_request": build_approval_request(
                    audience=SETTINGS.approval_audience or "",
                    tool=tool,
                    action=action,
                    params=params,
                    ttl_seconds=SETTINGS.approval_ttl_seconds,
                    risk_tier=decision.risk_tier.value,
                    reason=decision.reason,
                    approver_url=SETTINGS.approver_url,
                    deliver_url=f"{SETTINGS.public_url}/approvals/deliver" if SETTINGS.public_url else None,
                ),
            }
            audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="approval_required", request=params, result=result, reason=decision.reason)
            return result
        try:
            claims = approvals.verify_and_consume(approval_token, tool=tool, action=action, params=params)
            approved_by = claims.approved_by
        except ApprovalError as exc:
            result = {"status": "approval_rejected", "policy": policy, "error": str(exc)}
            audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="denied", request=params, result=result, reason=str(exc))
            return result

    try:
        result = redact(await operation(), max_chars=SETTINGS.max_response_chars)
    except UpstreamError as exc:
        result = {"status": "upstream_error", "error": str(exc)}
        if approved_by is not None:
            result["approval_consumed"] = True
            result["note"] = "The approval was spent on this attempt; a retry needs a new approval."
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="error", request=params, result=result, approved_by=approved_by, reason=str(exc))
        return result

    wrapped = {"status": "executed", "policy": policy, "approved_by": approved_by, "result": result}
    audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="success", request=params, result=result, approved_by=approved_by)
    return wrapped


@mcp.tool()
def operations_policy() -> dict[str, Any]:
    """Return the effective risk model: built-in tiers tightened by the operator policy file."""
    overlay = policy_module.ACTIVE_OVERLAY
    return {
        "environment": SETTINGS.environment,
        "approval_audience": SETTINGS.approval_audience,
        "writes_enabled": SETTINGS.writes_enabled,
        "low_autonomous": sorted(LOW_RISK_ACTIONS - overlay.forbid),
        "medium_conditional": sorted(MEDIUM_RISK_ACTIONS - overlay.forbid - overlay.require_approval),
        "medium_always_approval": sorted(overlay.require_approval - overlay.forbid),
        "high_approval_required": sorted(HIGH_RISK_ACTIONS - overlay.forbid),
        "forbidden_even_with_approval": sorted(FORBIDDEN_ACTIONS),
        "forbidden_by_operator_policy": sorted(overlay.forbid),
        "min_healthy_replicas_for_autonomy": overlay.min_healthy_replicas,
        "operator_policy_file": str(SETTINGS.policy_file) if SETTINGS.policy_file else None,
        "database_write_tools_exposed": False,
        "arbitrary_shell_exposed": False,
        "secret_value_tools_exposed": False,
        "docker_gate_credential_classes": ["read", "act"],
        "docker_socket_held_by_mcp": False,
        "container_exec_create_remove_exposed": False,
    }


@mcp.tool()
def evaluate_operation(action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify a proposed operation before attempting it. Unknown actions fail closed."""
    trusted_context = dict(context or {})
    trusted_context["environment"] = SETTINGS.environment
    return _decision_dict(evaluate(action, trusted_context))



@mcp.tool()
async def infrastructure_overview() -> dict[str, Any]:
    """Read the Docker host summary, managed containers and public health probes. No secret values are returned."""
    async def collect() -> dict[str, Any]:
        host, containers, health = await asyncio.gather(docker.host(), docker.list_containers(), veklom.health_matrix())
        return {
            "proof_state": "RUNTIME_OBSERVED",
            "host": host,
            "containers": containers,
            "public_health": health,
        }
    return await _read_call(tool="infrastructure_overview", action="infra.topology.read", params={}, operation=collect)


@mcp.tool()
async def health_matrix() -> dict[str, Any]:
    """Probe the configured public health endpoints without upgrading failures into healthy claims."""
    return await _read_call(tool="health_matrix", action="infra.health.read", params={}, operation=veklom.health_matrix)


@mcp.tool()
async def security_posture() -> dict[str, Any]:
    """Read the configured security-posture endpoint when it is live; otherwise return UNVERIFIED or NOT_CONFIGURED."""
    return await _read_call(tool="security_posture", action="security.posture.read", params={}, operation=veklom.security_posture)


@mcp.tool()
async def docker_host_info() -> Any:
    """Read Docker host identity, version and container counts."""
    return await _read_call(tool="docker_host_info", action="infra.topology.read", params={}, operation=docker.host)


@mcp.tool()
async def list_containers() -> Any:
    """List containers that opted in with the managed label. Unlabelled containers are invisible by design."""
    return await _read_call(tool="list_containers", action="infra.resources.read", params={}, operation=docker.list_containers)


@mcp.tool()
async def get_container(container: str) -> Any:
    """Inspect one managed container: image, state, health and allowlisted labels. Never env values, mounts or args."""
    params = {"container": container}
    return await _read_call(tool="get_container", action="infra.resources.read", params=params, operation=lambda: docker.get_container(container))


@mcp.tool()
async def get_container_env_presence(container: str) -> Any:
    """Return environment-variable NAMES for a managed container. Values are discarded inside the Docker gate."""
    params = {"container": container}
    return await _read_call(tool="get_container_env_presence", action="environment.presence.read", params=params, operation=lambda: docker.container_env_names(container))


@mcp.tool()
async def get_container_logs(container: str, lines: int = 100) -> Any:
    """Read a capped, redacted tail of a managed container's logs."""
    capped = max(1, min(lines, SETTINGS.max_log_lines))
    params = {"container": container, "lines": capped}
    return await _read_call(tool="get_container_logs", action="infra.logs.read", params=params, operation=lambda: docker.container_logs(container, capped))


@mcp.tool()
def verify_mcp_audit_chain(anchor_head: str | None = None) -> dict[str, Any]:
    """Verify the hash chain covering MCP reads, denials, approvals and mutations.

    Pass an anchor_head recorded earlier outside this server to also prove no newer events were
    deleted and the ledger was not replaced.
    """
    return audit.verify(anchor_head=anchor_head)


@mcp.tool()
async def wait_for_approval(request_id: str, timeout_seconds: int = 90) -> dict[str, Any]:
    """Wait for a human to approve a pending call on their approver device (up to 120 s).

    When state is "approved", repeat the exact same tool call with the same arguments; it runs once.
    Approving happens only on the human's device; this tool cannot approve anything.
    """
    deadline = asyncio.get_running_loop().time() + max(1, min(timeout_seconds, 120))
    while True:
        status = inbox.status(request_id)
        if status["state"] == "approved":
            return {**status, "next": "Repeat the exact same tool call now; it will run once."}
        if asyncio.get_running_loop().time() >= deadline:
            return {**status, "next": "Still waiting. Ask the human to open approve_url, then call wait_for_approval again."}
        await asyncio.sleep(1)


@mcp.tool()
def recent_mcp_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    """Read recent metadata-only MCP audit events. Arguments/results are represented by hashes."""
    return audit.tail(limit)


async def _restart_context(container: str) -> dict[str, Any]:
    """Derive redundancy facts from observed container health, never from agent-supplied claims."""
    detail = await docker.get_container(container)
    replicas = await docker.service_replicas(detail)
    return {
        "environment": SETTINGS.environment,
        "service": replicas["service"],
        "replicas": replicas["replicas"],
        "healthy_replicas": replicas["healthy_replicas"],
        "affects_single_instance": True,
        "causes_downtime": replicas["healthy_replicas"] < 2,
        "changes_effective_config": False,
        "active_incident": False,
    }


@mcp.tool()
async def restart_container(container: str, approval_token: str | None = None) -> Any:
    """Restart a managed container. Medium risk: autonomous only when other healthy replicas of the same compose service keep serving; otherwise approval is required."""
    params = {"container": container}
    try:
        context = await _restart_context(container)
    except UpstreamError as exc:
        context = {"environment": SETTINGS.environment, "affects_single_instance": True, "causes_downtime": True, "context_error": str(exc)}
    return await _write_call(tool="restart_container", action="service.restart", params=params, context=context, approval_token=approval_token, operation=lambda: docker.restart(container))


@mcp.tool()
async def stop_container(container: str, approval_token: str | None = None) -> Any:
    """Stop a managed container. High risk and always requires a one-time external approval."""
    params = {"container": container}
    return await _write_call(tool="stop_container", action="service.stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: docker.stop(container))


@mcp.tool()
async def start_stopped_container(container: str, approval_token: str | None = None) -> Any:
    """Start a deliberately stopped managed container. High risk and always requires a one-time external approval."""
    params = {"container": container}
    return await _write_call(tool="start_stopped_container", action="service.start_after_stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: docker.start(container))
