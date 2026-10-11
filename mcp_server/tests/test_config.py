from dataclasses import replace

import pytest

from veklom_ops_mcp.config import SETTINGS, parse_health_targets


def test_generic_profile_has_no_vendor_health_targets():
    assert replace(SETTINGS, profile="generic", health_targets_json=None).health_targets == {}
    assert replace(SETTINGS, profile="generic", security_posture_url=None).posture_url is None


def test_veklom_profile_keeps_legacy_targets():
    targets = replace(SETTINGS, profile="veklom", health_targets_json=None).health_targets
    assert set(targets) == {"byos", "cappo", "pgl", "capi"}  # legacy Control Plane is retired


def test_health_targets_parse_both_forms():
    targets = parse_health_targets('{"api": "https://api.acme.dev", "web": {"base_url": "https://acme.dev/", "paths": ["/", "/status"]}}')
    assert targets == {"api": ("https://api.acme.dev", ("/health",)), "web": ("https://acme.dev", ("/", "/status"))}


@pytest.mark.parametrize("raw", ['["x"]', '{"a": "ftp://x"}', '{"a": {"base_url": "https://x", "paths": ["nope"]}}', "{bad"])
def test_bad_health_targets_fail_at_startup(raw):
    with pytest.raises(RuntimeError):
        parse_health_targets(raw)


def test_write_mode_requires_audience():
    settings = replace(
        SETTINGS,
        access_token="t",
        writes_enabled=True,
        docker_gate_read_token="r",
        docker_gate_act_token="a",
        approval_public_key_b64="pk",
        approval_audience=None,
    )
    with pytest.raises(RuntimeError, match="VEKLOM_MCP_APPROVAL_AUDIENCE"):
        settings.validate()


def test_write_mode_requires_separate_gate_tokens():
    settings = replace(
        SETTINGS,
        access_token="t",
        writes_enabled=True,
        docker_gate_read_token="same",
        docker_gate_act_token="same",
        approval_public_key_b64="pk",
        approval_audience="acme-prod",
    )
    with pytest.raises(RuntimeError, match="different credentials"):
        settings.validate()


def test_transport_security_follows_allowed_hosts():
    from veklom_ops_mcp.tools import transport_security

    assert transport_security([], []).enable_dns_rebinding_protection is False
    configured = transport_security(["ops.example.com"], [])
    assert configured.enable_dns_rebinding_protection is True
    assert configured.allowed_hosts == ["ops.example.com", "ops.example.com:*"]
    assert configured.allowed_origins == ["https://ops.example.com"]


def test_write_mode_requires_act_token():
    settings = replace(SETTINGS, access_token="t", writes_enabled=True, docker_gate_act_token=None, approval_public_key_b64="pk", approval_audience="a")
    with pytest.raises(RuntimeError, match="DOCKER_GATE_ACT_TOKEN"):
        settings.validate()
