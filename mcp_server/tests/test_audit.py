from dataclasses import replace

from veklom_ops_mcp.audit import AuditLedger
from veklom_ops_mcp.config import SETTINGS


def ledger(tmp_path):
    settings = replace(SETTINGS, audit_store=tmp_path / "audit.jsonl")
    return AuditLedger(settings)


def test_hash_chain_verifies(tmp_path):
    audit = ledger(tmp_path)
    audit.append(
        tool="health",
        action="infra.health.read",
        risk_tier="low",
        outcome="success",
        request={},
        result={"ok": True},
    )
    audit.append(
        tool="restart",
        action="service.restart",
        risk_tier="medium",
        outcome="approval_required",
        request={"application_uuid": "app-1"},
        result={"status": "approval_required"},
    )
    result = audit.verify()
    assert result["valid"] is True
    assert result["events"] == 2


def test_tampering_breaks_chain(tmp_path):
    audit = ledger(tmp_path)
    audit.append(
        tool="health",
        action="infra.health.read",
        risk_tier="low",
        outcome="success",
        request={},
        result={"ok": True},
    )
    text = audit.path.read_text(encoding="utf-8")
    audit.path.write_text(text.replace('"outcome":"success"', '"outcome":"failure"'), encoding="utf-8")
    result = audit.verify()
    assert result["valid"] is False
    assert result["reason"] == "event_hash_mismatch"


def test_raw_request_and_result_are_not_persisted(tmp_path):
    audit = ledger(tmp_path)
    audit.append(
        tool="logs",
        action="infra.logs.read",
        risk_tier="low",
        outcome="success",
        request={"query": "sensitive-input"},
        result={"text": "sensitive-output"},
    )
    text = audit.path.read_text(encoding="utf-8")
    assert "sensitive-input" not in text
    assert "sensitive-output" not in text
    assert "request_sha256" in text
    assert "result_sha256" in text
