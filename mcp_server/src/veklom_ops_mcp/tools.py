from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from .approval import ApprovalAuthority, ApprovalError, params_hash
from .audit import AuditLedger
from .clients import CoolifyClient, UpstreamError, VeklomClient
from .config import SETTINGS
from .policy import (
    FORBIDDEN_ACTIONS,
    HIGH_RISK_ACTIONS,
    LOW_RISK_ACTIONS,
    MEDIUM_RISK_ACTIONS,
    PolicyDecision,
    evaluate,
)
from .redaction import redact

mcp = FastMCP(
    SETTINGS.service_name,
    instructions=(
        "Veklom governed operations plane. Read tools are least-authority. "
        "State-changing tools are risk-classified, approval-gated when required, "
        "and every call is hash-chain audited. Never request or reveal secret values."
    ),
    stateless_http=True,
    json_response=True,
)

coolify = CoolifyClient()
veklom = VeklomClient()
audit = AuditLedger()
approvals = ApprovalAuthority()


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
            result = {
                "status": "approval_required",
                "policy": policy,
                "approval_request": {
                    "action": action,
                    "params_sha256": params_hash(params),
                    "expires_after_seconds": SETTINGS.approval_ttl_seconds,
                    "note": "Approval must be minted outside this MCP by the founder or a separately trusted coding-agent environment.",
                },
            }
            audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="approval_required", request=params, result=result, reason=decision.reason)
            return result
        try:
            claims = approvals.verify_and_consume(approval_token, action, params)
            approved_by = claims.approved_by
        except ApprovalError as exc:
            result = {"status": "approval_rejected", "policy": policy, "error": str(exc)}
            audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="denied", request=params, result=result, reason=str(exc))
            return result

    try:
        result = redact(await operation(), max_chars=SETTINGS.max_response_chars)
    except UpstreamError as exc:
        result = {"status": "upstream_error", "error": str(exc)}
        audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="error", request=params, result=result, approved_by=approved_by, reason=str(exc))
        return result

    wrapped = {"status": "executed", "policy": policy, "approved_by": approved_by, "result": result}
    audit.append(tool=tool, action=action, risk_tier=decision.risk_tier.value, outcome="success", request=params, result=result, approved_by=approved_by)
    return wrapped


@mcp.tool()
def operations_policy() -> dict[str, Any]:
    """Return the MCP risk model and non-bypassable forbidden actions."""
    return {
        "environment": SETTINGS.environment,
        "writes_enabled": SETTINGS.writes_enabled,
        "low_autonomous": sorted(LOW_RISK_ACTIONS),
        "medium_conditional": sorted(MEDIUM_RISK_ACTIONS),
        "high_approval_required": sorted(HIGH_RISK_ACTIONS),
        "forbidden_even_with_approval": sorted(FORBIDDEN_ACTIONS),
        "database_write_tools_exposed": False,
        "arbitrary_shell_exposed": False,
        "secret_value_tools_exposed": False,
        "coolify_credential_classes": ["read", "deploy"],
        "coolify_write_or_root_credentials_required": False,
    }


@mcp.tool()
def evaluate_operation(action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify a proposed operation before attempting it. Unknown actions fail closed."""
    trusted_context = dict(context or {})
    trusted_context["environment"] = SETTINGS.environment
    return _decision_dict(evaluate(action, trusted_context))


@mcp.tool()
async def infrastructure_overview() -> dict[str, Any]:
    """Read a safe-projected inventory plus live Veklom health. No secret values are returned."""
    async def collect() -> dict[str, Any]:
        servers, applications, databases, services, deployments, health = await asyncio.gather(
            coolify.list_servers(), coolify.list_applications(), coolify.list_databases(),
            coolify.list_services(), coolify.list_deployments(), veklom.health_matrix(),
        )
        return {
            "proof_state": "RUNTIME_OBSERVED",
            "servers": servers,
            "applications": applications,
            "databases": databases,
            "services": services,
            "deployments": deployments,
            "veklom_health": health,
        }
    return await _read_call(tool="infrastructure_overview", action="infra.topology.read", params={}, operation=collect)


@mcp.tool()
async def veklom_health_matrix() -> dict[str, Any]:
    """Probe canonical public service health without upgrading failures into healthy claims."""
    return await _read_call(tool="veklom_health_matrix", action="infra.health.read", params={}, operation=veklom.health_matrix)


@mcp.tool()
async def security_posture() -> dict[str, Any]:
    """Read the Veklom M2M security-posture endpoint when it is live; otherwise return UNVERIFIED."""
    return await _read_call(tool="security_posture", action="security.posture.read", params={}, operation=veklom.security_posture)


@mcp.tool()
async def list_servers() -> Any:
    """List safe-projected Coolify server topology without keys, tokens, proxy config bodies, or validation logs."""
    return await _read_call(tool="list_servers", action="infra.topology.read", params={}, operation=coolify.list_servers)


@mcp.tool()
async def get_server(server_uuid: str) -> Any:
    """Inspect one server through an explicit safe-field projection."""
    params = {"server_uuid": server_uuid}
    return await _read_call(tool="get_server", action="infra.topology.read", params=params, operation=lambda: coolify.get_server(server_uuid))


@mcp.tool()
async def get_server_resources(server_uuid: str) -> Any:
    """List resource identity/type/status for one server without exposing resource configuration bodies."""
    params = {"server_uuid": server_uuid}
    return await _read_call(tool="get_server_resources", action="infra.topology.read", params=params, operation=lambda: coolify.server_resources(server_uuid))


@mcp.tool()
async def get_server_domains(server_uuid: str) -> Any:
    """Read the domain names Coolify associates with a server for topology/drift analysis."""
    params = {"server_uuid": server_uuid}
    return await _read_call(tool="get_server_domains", action="infra.routes.read", params=params, operation=lambda: coolify.server_domains(server_uuid))


@mcp.tool()
async def list_applications() -> Any:
    """List Coolify applications through a safe-field projection and read-only credential."""
    return await _read_call(tool="list_applications", action="infra.resources.read", params={}, operation=coolify.list_applications)


@mcp.tool()
async def get_application(application_uuid: str) -> Any:
    """Inspect one application using an explicit safe-field projection."""
    params = {"application_uuid": application_uuid}
    return await _read_call(tool="get_application", action="infra.resources.read", params=params, operation=lambda: coolify.get_application(application_uuid))


@mcp.tool()
async def get_application_env_presence(application_uuid: str) -> Any:
    """Return environment-variable names/flags only. Values and real_values are structurally discarded."""
    params = {"application_uuid": application_uuid}
    return await _read_call(tool="get_application_env_presence", action="environment.presence.read", params=params, operation=lambda: coolify.application_env_presence(application_uuid))


@mcp.tool()
async def get_application_logs(application_uuid: str, lines: int = 100) -> Any:
    """Read a capped tail of application logs with credential/token redaction."""
    capped = max(1, min(lines, SETTINGS.max_log_lines))
    params = {"application_uuid": application_uuid, "lines": capped}
    return await _read_call(tool="get_application_logs", action="infra.logs.read", params=params, operation=lambda: coolify.application_logs(application_uuid, capped))


@mcp.tool()
async def list_databases() -> Any:
    """Read database resource metadata only. This MCP exposes no database mutation or arbitrary SQL tool."""
    return await _read_call(tool="list_databases", action="database.schema.read", params={}, operation=coolify.list_databases)


@mcp.tool()
async def get_database(database_uuid: str) -> Any:
    """Read safe-projected database metadata only; never credentials, URLs, SQL, or data mutation."""
    params = {"database_uuid": database_uuid}
    return await _read_call(tool="get_database", action="database.schema.read", params=params, operation=lambda: coolify.get_database(database_uuid))


@mcp.tool()
async def get_database_backups(database_uuid: str) -> Any:
    """Inspect database backup configuration/status without creating, restoring, triggering, or deleting backups."""
    params = {"database_uuid": database_uuid}
    return await _read_call(tool="get_database_backups", action="database.read", params=params, operation=lambda: coolify.database_backups(database_uuid))


@mcp.tool()
async def list_services() -> Any:
    """List Coolify service stacks through a safe-field projection."""
    return await _read_call(tool="list_services", action="infra.resources.read", params={}, operation=coolify.list_services)


@mcp.tool()
async def get_service(service_uuid: str) -> Any:
    """Inspect one Coolify service stack without compose bodies or environment values."""
    params = {"service_uuid": service_uuid}
    return await _read_call(tool="get_service", action="infra.resources.read", params=params, operation=lambda: coolify.get_service(service_uuid))


@mcp.tool()
async def get_service_logs(service_uuid: str, lines: int = 100) -> Any:
    """Read a capped, redacted tail of service-stack logs."""
    capped = max(1, min(lines, SETTINGS.max_log_lines))
    params = {"service_uuid": service_uuid, "lines": capped}
    return await _read_call(tool="get_service_logs", action="infra.logs.read", params=params, operation=lambda: coolify.service_logs(service_uuid, capped))


@mcp.tool()
async def list_deployments() -> Any:
    """Read active deployment state without deployment log bodies."""
    return await _read_call(tool="list_deployments", action="infra.deployments.read", params={}, operation=coolify.list_deployments)


@mcp.tool()
async def get_deployment(deployment_uuid: str) -> Any:
    """Read one safe-projected deployment record."""
    params = {"deployment_uuid": deployment_uuid}
    return await _read_call(tool="get_deployment", action="infra.deployments.read", params=params, operation=lambda: coolify.get_deployment(deployment_uuid))


@mcp.tool()
def verify_mcp_audit_chain() -> dict[str, Any]:
    """Verify the local hash chain covering MCP reads, denials, approvals and mutations."""
    return audit.verify()


@mcp.tool()
def recent_mcp_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    """Read recent metadata-only MCP audit events. Arguments/results are represented by hashes."""
    return audit.tail(limit)


async def _application_medium_context(application_uuid: str, *, same_artifact: bool = False) -> dict[str, Any]:
    app = await coolify.get_application(application_uuid)
    replicas = app.get("swarm_replicas") if isinstance(app, dict) else None
    return {
        "environment": SETTINGS.environment,
        "healthy_replicas": replicas if isinstance(replicas, int) and replicas > 0 else None,
        "affects_single_instance": not isinstance(replicas, int) or replicas < 2,
        "causes_downtime": False,
        "changes_effective_config": False,
        "same_artifact": same_artifact,
        "artifact_digest_verified": False,
        "active_incident": False,
    }


async def _service_medium_context(service_uuid: str) -> dict[str, Any]:
    await coolify.get_service(service_uuid)
    return {
        "environment": SETTINGS.environment,
        "healthy_replicas": None,
        "affects_single_instance": True,
        "causes_downtime": False,
        "changes_effective_config": False,
        "active_incident": False,
    }


@mcp.tool()
async def restart_application(application_uuid: str, approval_token: str | None = None) -> Any:
    """Restart an application. Medium risk: autonomous only when runtime guardrails prove it safe; otherwise approval is required."""
    params = {"application_uuid": application_uuid}
    try:
        context = await _application_medium_context(application_uuid)
    except UpstreamError as exc:
        context = {"environment": SETTINGS.environment, "affects_single_instance": True, "causes_downtime": True, "context_error": str(exc)}
    return await _write_call(tool="restart_application", action="service.restart", params=params, context=context, approval_token=approval_token, operation=lambda: coolify.restart_application(application_uuid))


@mcp.tool()
async def restart_service(service_uuid: str, approval_token: str | None = None) -> Any:
    """Restart a Coolify service stack. Medium risk; production ambiguity falls to approval."""
    params = {"service_uuid": service_uuid}
    try:
        context = await _service_medium_context(service_uuid)
    except UpstreamError as exc:
        context = {"environment": SETTINGS.environment, "affects_single_instance": True, "causes_downtime": True, "context_error": str(exc)}
    return await _write_call(tool="restart_service", action="service.restart", params=params, context=context, approval_token=approval_token, operation=lambda: coolify.restart_service(service_uuid))


@mcp.tool()
async def redeploy_application_same_source(application_uuid: str, approval_token: str | None = None) -> Any:
    """Request a normal redeploy. Until the exact deployed artifact digest is independently proven unchanged, this medium-risk action escalates to approval."""
    params = {"application_uuid": application_uuid, "force": False}
    try:
        context = await _application_medium_context(application_uuid, same_artifact=True)
    except UpstreamError as exc:
        context = {"environment": SETTINGS.environment, "affects_single_instance": True, "causes_downtime": True, "same_artifact": False, "artifact_digest_verified": False, "context_error": str(exc)}
    return await _write_call(tool="redeploy_application_same_source", action="service.redeploy_same_commit", params=params, context=context, approval_token=approval_token, operation=lambda: coolify.deploy(application_uuid, force=False))


@mcp.tool()
async def cancel_deployment(deployment_uuid: str, approval_token: str | None = None) -> Any:
    """Cancel a deployment. Queued work may be autonomous; interrupting active production work falls to approval."""
    params = {"deployment_uuid": deployment_uuid}
    try:
        deployment = await coolify.get_deployment(deployment_uuid)
        status = str(deployment.get("status", "unknown")).lower() if isinstance(deployment, dict) else "unknown"
        active = status not in {"queued", "pending", "finished", "failed", "cancelled", "cancelled-by-user"}
    except UpstreamError:
        active = True
    context = {
        "environment": SETTINGS.environment,
        "affects_single_instance": active,
        "healthy_replicas": None,
        "causes_downtime": active,
        "changes_effective_config": False,
        "active_incident": False,
    }
    return await _write_call(tool="cancel_deployment", action="deployment.cancel", params=params, context=context, approval_token=approval_token, operation=lambda: coolify.cancel_deployment(deployment_uuid))


@mcp.tool()
async def stop_application(application_uuid: str, approval_token: str | None = None) -> Any:
    """Stop an application. High risk and always requires a one-time external approval."""
    params = {"application_uuid": application_uuid}
    return await _write_call(tool="stop_application", action="service.stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: coolify.stop_application(application_uuid))


@mcp.tool()
async def start_stopped_application(application_uuid: str, approval_token: str | None = None) -> Any:
    """Start a deliberately stopped application. High risk and always requires a one-time external approval."""
    params = {"application_uuid": application_uuid}
    return await _write_call(tool="start_stopped_application", action="service.start_after_stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: coolify.start_application(application_uuid))


@mcp.tool()
async def stop_service(service_uuid: str, approval_token: str | None = None) -> Any:
    """Stop a Coolify service stack. High risk and always requires a one-time external approval."""
    params = {"service_uuid": service_uuid}
    return await _write_call(tool="stop_service", action="service.stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: coolify.stop_service(service_uuid))


@mcp.tool()
async def start_stopped_service(service_uuid: str, approval_token: str | None = None) -> Any:
    """Start a deliberately stopped service stack. High risk and always requires a one-time external approval."""
    params = {"service_uuid": service_uuid}
    return await _write_call(tool="start_stopped_service", action="service.start_after_stop", params=params, context={"environment": SETTINGS.environment}, approval_token=approval_token, operation=lambda: coolify.start_service(service_uuid))
