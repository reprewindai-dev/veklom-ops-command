#!/usr/bin/env python3
"""Run the public WebMCP consequence lifecycle from a separately provisioned host.

This verifier refuses to mutate the public sandbox unless its runner provenance
is supplied and its host/network checks pass. It never writes mount tokens or
nonces to the evidence file. A local run is not an independent reproduction.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import os
import platform
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


TIMEOUT_SECONDS = 20
PACKAGE_REF = "veklom.governed-counter@v1"
CONSEQUENCE_TOOLS = {
    "veklom_mount_capability",
    "veklom_execute_action",
    "veklom_read_target_state",
    "veklom_verify_evidence",
    "veklom_terminate_mount",
}
REDACT_KEYS = {
    "access_token",
    "refresh_token",
    "token",
    "token_id",
    "nonce",
    "authorization",
    "cookie",
    "signature",
    "private_key",
    "password",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in REDACT_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def find_field(value: Any, field_names: tuple[str, ...]) -> Any | None:
    if isinstance(value, dict):
        for name in field_names:
            if value.get(name) not in (None, ""):
                return value[name]
        for item in value.values():
            found = find_field(item, field_names)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_field(item, field_names)
            if found is not None:
                return found
    return None


def find_named_field(value: Any, field_names: tuple[str, ...]) -> tuple[str, Any] | None:
    """Return the matching field name as well as its value."""
    if isinstance(value, dict):
        for name in field_names:
            candidate = value.get(name)
            if candidate not in (None, ""):
                return name, candidate
        for item in value.values():
            found = find_named_field(item, field_names)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_named_field(item, field_names)
            if found is not None:
                return found
    return None


def parse_tool_payload(result: dict[str, Any]) -> Any:
    if result.get("isError"):
        raise RuntimeError("MCP tool returned isError=true")
    structured = result.get("structuredContent")
    if isinstance(structured, (dict, list)):
        return structured
    for block in result.get("content", []):
        text = block.get("text") if isinstance(block, dict) else None
        if not isinstance(text, str):
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    raise RuntimeError("MCP tool response did not contain structured JSON")


def state_value(payload: Any) -> int:
    value = find_field(payload, ("value",))
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("Target readback did not expose an integer state value")
    return value


def decision(payload: Any) -> str:
    result = find_field(payload, ("decision",))
    return str(result).lower() if result is not None else ""


def assert_equal(label: str, actual: Any, expected: Any, report: dict[str, Any]) -> None:
    passed = actual == expected
    report["checks"].append({
        "name": label,
        "result": "PASS" if passed else "FAIL",
        "observed": redact(actual),
        "expected": redact(expected),
    })
    if not passed:
        raise RuntimeError(f"Invariant failed: {label}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PublicMCP:
    def __init__(self, base_url: str, report: dict[str, Any]):
        self.base_url = base_url.rstrip("/")
        self.endpoint = self.base_url + "/api/mcp"
        self.report = report
        self._id = 0
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            NoRedirect(),
        )

    def request_json(self, url: str, method: str = "GET", body: Any | None = None) -> Any:
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Veklom-External-WebMCP-Verifier/1.0",
            },
        )
        status = None
        headers: Any = {}
        try:
            with self._opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.status
                headers = response.headers
                raw = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            headers = exc.headers
            raw = exc.read()
        self.report["http_trace"].append({
            "method": method,
            "url": url,
            "status": status,
            "cf_ray": headers.get("CF-Ray") if headers else None,
            "date": headers.get("Date") if headers else None,
            "content_type": headers.get("Content-Type") if headers else None,
            "tls": "HTTPS with default certificate validation" if url.startswith("https://") else "NOT_TLS",
        })
        if status != 200:
            raise RuntimeError(f"HTTP request failed with status {status}")
        return json.loads(raw.decode("utf-8"))

    def rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        response = self.request_json(self.endpoint, "POST", payload)
        if response.get("error"):
            raise RuntimeError(f"JSON-RPC {method} returned an error object")
        return response

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        response = self.rpc("tools/call", {"name": name, "arguments": arguments})
        return parse_tool_payload(response.get("result", {}))


def local_addresses() -> list[str]:
    found: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, type=socket.SOCK_STREAM):
            ip = item[4][0].split("%", 1)[0]
            parsed = ipaddress.ip_address(ip)
            if not parsed.is_loopback and not parsed.is_unspecified:
                found.add(ip)
    except OSError:
        pass
    return sorted(found)


def provenance(args: argparse.Namespace) -> dict[str, Any]:
    addresses = local_addresses()
    blocked_networks = [ipaddress.ip_network(value, strict=False) for value in args.veklom_network_cidr]
    overlaps = []
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if any(parsed.version == net.version and parsed in net for net in blocked_networks):
            overlaps.append(address)
    hostname = socket.gethostname()
    hardware_hostname = args.veklom_hardware_hostname.strip()
    excluded = {value.lower().rstrip(".") for value in [*args.veklom_hostname, hardware_hostname] if value.strip()}
    is_container = Path("/.dockerenv").exists() or bool(os.environ.get("KUBERNETES_SERVICE_HOST"))
    provider = args.runner_provider.strip()
    github_actions = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    github_run_id = os.environ.get("GITHUB_RUN_ID", "")
    github_identity_confirmed = provider.lower() != "github-actions" or (
        github_actions and bool(github_run_id) and args.runner_id.strip() == github_run_id
    )
    checks = {
        "runner_provider_present": bool(provider),
        "runner_id_present": bool(args.runner_id.strip()),
        "production_hardware_hostname_present": bool(hardware_hostname),
        "known_deployment_hostname_present": bool(args.veklom_hostname),
        "hostname_differs_from_deployment": hostname.lower().rstrip(".") not in excluded,
        "not_a_container": not is_container,
        "local_addresses_observed": bool(addresses),
        "no_address_in_veklom_network": not overlaps,
        "github_runner_identity_matches_environment": github_identity_confirmed,
    }
    return {
        "provider": provider,
        "runner_id": args.runner_id,
        "github_run_id": github_run_id or None,
        "github_repository": os.environ.get("GITHUB_REPOSITORY"),
        "recorded_production_hardware_hostname": hardware_hostname,
        "hostname": hostname,
        "platform": platform.platform(),
        "runner_os": platform.system(),
        "runner_release": platform.release(),
        "github_actions": github_actions,
        "container_detected": is_container,
        "local_addresses": addresses,
        "veklom_private_networks": args.veklom_network_cidr,
        "addresses_overlapping_veklom_network": overlaps,
        "excluded_deployment_hostnames": sorted(excluded),
        "checks": checks,
        "eligible_as_independent_runner": all(checks.values()),
        "public_source_ip": os.environ.get("VEKLOM_VERIFIER_SOURCE_IP"),
        "public_source_ip_method": "provided by runner environment" if os.environ.get("VEKLOM_VERIFIER_SOURCE_IP") else "not provided",
    }


def discover_target(base_url: str) -> tuple[list[str], list[str]]:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise RuntimeError("base URL must be an HTTPS origin")
    try:
        addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)})
    except OSError as exc:
        raise RuntimeError("DNS resolution failed for target") from exc
    return addresses, [parsed.hostname]


def tools_names(payload: Any) -> list[str]:
    tools = payload.get("tools") if isinstance(payload, dict) else None
    if not isinstance(tools, list):
        raise RuntimeError("Tool catalog is missing its tools array")
    return sorted(item["name"] for item in tools if isinstance(item, dict) and isinstance(item.get("name"), str))


def extract_mount_fields(mount: Any) -> tuple[str, str, str]:
    if not isinstance(mount, dict):
        raise RuntimeError("Mount response was not an object")
    mount_record = mount.get("mount")
    token_record = mount.get("token")
    mount_id = (
        mount_record.get("id") if isinstance(mount_record, dict) else None
    ) or mount.get("mount_id")
    token_id = (
        token_record.get("token_id") if isinstance(token_record, dict) else None
    ) or mount.get("token_id")
    nonce = (
        token_record.get("nonce") if isinstance(token_record, dict) else None
    ) or mount.get("nonce")
    if not all(isinstance(item, str) and item for item in (mount_id, token_id, nonce)):
        raise RuntimeError("Mount response did not expose mount id, token id, and nonce")
    return mount_id, token_id, nonce


def extract_evidence_reference(payload: Any) -> tuple[str, str]:
    found = find_named_field(
        payload,
        ("receipt_id", "event_hash", "evidence_hash", "decision_hash", "receipt"),
    )
    if found is None or not isinstance(found[1], str):
        raise RuntimeError("Allowed action returned no evidence reference")
    return found


def evidence_verification_succeeded(payload: Any) -> bool:
    for name in ("verified", "valid"):
        found = find_field(payload, (name,))
        if found is True:
            return True
    for name in ("status", "decision"):
        found = find_field(payload, (name,))
        if isinstance(found, str) and found.lower() in {"confirmed", "verified"}:
            return True
    return False


def build_action_arguments(mount_id: str, token_id: str, nonce: str, action: str, workspace: str) -> dict[str, Any]:
    return {
        "mount_id": mount_id,
        "token_id": token_id,
        "nonce": nonce,
        "action": action,
        "target_ref": "activation.governed-counter",
        "resource": "counter",
        "arguments": {},
        "workspace": workspace,
    }


def verify(args: argparse.Namespace, report: dict[str, Any]) -> None:
    base_url = args.base_url.rstrip("/")
    dns, target_hosts = discover_target(base_url)
    report["target"] = {
        "base_url": base_url,
        "hostname": target_hosts[0],
        "dns_addresses": dns,
    }
    client = PublicMCP(base_url, report)
    live = client.rpc("tools/list").get("result", {})
    live_names = tools_names(live)
    static = client.request_json(base_url + "/mcp/tools.json")
    static_names = tools_names(static)
    assert_equal("live tool catalog matches static catalog", live_names, static_names, report)
    assert_equal(
        "required consequence tools are present",
        CONSEQUENCE_TOOLS.issubset(set(live_names)),
        True,
        report,
    )
    report["tool_names"] = live_names

    discovery = client.call_tool("veklom_discover_capabilities", {})
    has_package = PACKAGE_REF in json.dumps(discovery)
    assert_equal("governed counter capability is discoverable", has_package, True, report)

    workspace = "external-verify-" + uuid.uuid4().hex[:16]
    report["synthetic_workspace"] = workspace

    def mount() -> tuple[str, str, str]:
        result = client.call_tool("veklom_mount_capability", {
            "package_ref": PACKAGE_REF,
            "workspace": workspace,
            "project": "external-verification",
            "reads": ["counter.read"],
            "writes": ["counter.increment"],
            "blocked": ["counter.reset"],
            "ttl_seconds": 300,
        })
        assert_equal("capability mount allowed", decision(result), "allow", report)
        mount_id, token_id, nonce = extract_mount_fields(result)
        report.setdefault("mounts", []).append({"mount_id": mount_id, "decision": "allow"})
        return mount_id, token_id, nonce

    mount1, token1, nonce1 = mount()
    mount2 = token2 = nonce2 = None
    active_mounts = [mount1]
    try:
        baseline = client.call_tool("veklom_read_target_state", {"mount_id": mount1, "workspace": workspace})
        v0 = state_value(baseline)
        report["baseline_value"] = v0

        success_arguments = build_action_arguments(mount1, token1, nonce1, "counter.increment", workspace)
        success_digest = canonical_hash(success_arguments)
        allowed = client.call_tool("veklom_execute_action", success_arguments)
        assert_equal("allowed action decision", decision(allowed), "allow", report)

        after_allowed = client.call_tool("veklom_read_target_state", {"mount_id": mount1, "workspace": workspace})
        v1 = state_value(after_allowed)
        assert_equal("allowed action changes target state by exactly one", v1, v0 + 1, report)

        receipt_key, receipt = extract_evidence_reference(allowed)
        verify_args = {"event_hash": receipt} if receipt_key.endswith("hash") else {"receipt_id": receipt}
        verified = client.call_tool("veklom_verify_evidence", verify_args)
        is_verified = evidence_verification_succeeded(verified)
        assert_equal("PGL evidence independently verifies", is_verified, True, report)
        report["evidence_reference"] = receipt

        mount2, token2, nonce2 = mount()
        active_mounts.append(mount2)
        forbidden_arguments = build_action_arguments(mount2, token2, nonce2, "counter.reset", workspace)
        forbidden = client.call_tool("veklom_execute_action", forbidden_arguments)
        assert_equal("forbidden action denied", decision(forbidden), "deny", report)
        after_forbidden = client.call_tool("veklom_read_target_state", {"mount_id": mount2, "workspace": workspace})
        v2 = state_value(after_forbidden)
        assert_equal("forbidden action leaves state unchanged", v2, v1, report)

        terminated = client.call_tool("veklom_terminate_mount", {"mount_id": mount1, "workspace": workspace})
        assert_equal("successful-action mount terminates", decision(terminated), "allow", report)
        active_mounts.remove(mount1)

        replay_arguments = copy.deepcopy(success_arguments)
        replay_digest = canonical_hash(replay_arguments)
        assert_equal("replay payload exactly matches previously allowed action", replay_digest, success_digest, report)
        replay = client.call_tool("veklom_execute_action", replay_arguments)
        assert_equal("exact action replay after termination denied", decision(replay), "deny", report)

        final_read = client.call_tool("veklom_read_target_state", {"mount_id": mount2, "workspace": workspace})
        v3 = state_value(final_read)
        assert_equal("exact replay causes zero additional mutation", v3, v2, report)
        report["action_payload_sha256"] = success_digest
    finally:
        for mount_id in reversed(active_mounts):
            try:
                client.call_tool("veklom_terminate_mount", {"mount_id": mount_id, "workspace": workspace, "reason": "external_verifier_cleanup"})
            except Exception:
                report.setdefault("cleanup", []).append({"mount_id": mount_id, "result": "terminate_failed"})


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://veklom.com")
    parser.add_argument("--runner-provider", required=True, help="e.g. github-actions or second-physical-machine")
    parser.add_argument("--runner-id", required=True, help="Unique runner/job identifier; do not put credentials here")
    parser.add_argument("--source-sha", required=True, type=source_sha_argument,
                        help="Exact 40- or 64-hex source commit under test")
    parser.add_argument("--runtime-ref", required=True, type=runtime_ref_argument,
                        help="Exact deployed image digest or deployment identifier; mutable tags are rejected")
    parser.add_argument("--veklom-hostname", action="append", required=True, help="Known Veklom runtime host; repeat if needed")
    parser.add_argument("--veklom-hardware-hostname", required=True,
                        help="Recorded hostname of the self-owned physical production host")
    parser.add_argument("--veklom-network-cidr", action="append", required=True, help="Known Veklom private network CIDR; repeat if needed")
    parser.add_argument("--evidence-out", type=Path, default=None)
    parser.add_argument("--confirm-governed-counter-write", action="store_true", required=True,
                        help="Explicitly confirm one synthetic governed-counter increment may be performed")
    return parser


def source_sha_argument(value: str) -> str:
    if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", value.strip()):
        raise argparse.ArgumentTypeError("source SHA must be exactly 40 or 64 hexadecimal characters")
    return value.strip().lower()


def runtime_ref_argument(value: str) -> str:
    normalized = value.strip()
    if not normalized or normalized.lower() in {"latest", "unknown", "unverified", "none"}:
        raise argparse.ArgumentTypeError("runtime ref must identify an exact deployed artifact, not a mutable/unknown label")
    return normalized


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    timestamp = utc_now()
    output = args.evidence_out or Path(f"external-webmcp-{timestamp.replace(':', '').replace('-', '')}.json")
    script_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report: dict[str, Any] = {
        "proof_id": "webmcp-external-" + uuid.uuid4().hex,
        "claim": "A public WebMCP governed-counter lifecycle can be externally reproduced.",
        "classification": "NOT_PROVED",
        "started_at": timestamp,
        "finished_at": None,
        "source_sha": args.source_sha,
        "runtime_ref": args.runtime_ref,
        "verifier_sha256": "sha256:" + script_sha,
        "runner": None,
        "target": None,
        "checks": [],
        "http_trace": [],
        "limitations": [
            "This verifier exercises only the public governed-counter sandbox capability.",
            "It does not establish Anchor/browser-provider integration or production settlement.",
        ],
    }
    try:
        report["runner"] = provenance(args)
        assert_equal(
            "runner is outside the recorded Veklom host and private networks",
            report["runner"]["eligible_as_independent_runner"],
            True,
            report,
        )
        verify(args, report)
        report["classification"] = "INDEPENDENTLY_REPRODUCED"
        exit_code = 0
    except Exception as exc:  # report a terminal failure without serializing response tokens
        report["classification"] = "FAILED"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)[:300]}
        exit_code = 1
    report["finished_at"] = utc_now()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(redact(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{report['classification']} proof_id={report['proof_id']} checks={sum(c['result'] == 'PASS' for c in report['checks'])}/{len(report['checks'])} artifact={output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
