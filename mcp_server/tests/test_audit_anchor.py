from dataclasses import replace

from veklom_ops_mcp.audit import AuditLedger
from veklom_ops_mcp.config import SETTINGS


def ledger(tmp_path):
    return AuditLedger(replace(SETTINGS, audit_store=tmp_path / "audit.jsonl", audit_anchor_url=None))


def write_events(audit, count):
    for i in range(count):
        audit.append(tool="stop_application", action="service.stop", risk_tier="high", outcome="success", request={"i": i})


def test_anchor_present_verifies(tmp_path):
    audit = ledger(tmp_path)
    write_events(audit, 2)
    anchor = audit.head()["head"]
    write_events(audit, 2)
    result = audit.verify(anchor_head=anchor)
    assert result["valid"] is True
    assert result["anchored"] is True


def test_tail_truncation_is_detected_against_anchor(tmp_path):
    audit = ledger(tmp_path)
    write_events(audit, 3)
    anchor = audit.head()["head"]
    lines = audit.path.read_text(encoding="utf-8").splitlines()
    audit.path.write_text(lines[0] + "\n", encoding="utf-8")
    assert audit.verify()["valid"] is True  # the bare chain cannot see this
    result = audit.verify(anchor_head=anchor)
    assert result["valid"] is False
    assert result["reason"] == "anchor_not_found"


def test_full_rewrite_is_detected_against_anchor(tmp_path):
    audit = ledger(tmp_path)
    write_events(audit, 1)
    anchor = audit.head()["head"]
    audit.path.unlink()
    audit.append(tool="list_servers", action="infra.topology.read", risk_tier="low", outcome="success", request={})
    assert audit.verify(anchor_head=anchor)["reason"] == "anchor_not_found"


def test_deleted_ledger_is_detected_against_anchor(tmp_path):
    audit = ledger(tmp_path)
    write_events(audit, 1)
    anchor = audit.head()["head"]
    audit.path.unlink()
    assert audit.verify(anchor_head=anchor)["valid"] is False


def test_anchor_webhook_receives_hashes_only(tmp_path, monkeypatch):
    sent = []
    monkeypatch.setattr("veklom_ops_mcp.audit.httpx.post", lambda url, **kw: sent.append((url, kw)))
    monkeypatch.setattr("veklom_ops_mcp.audit.threading.Thread", _InlineThread)
    audit = AuditLedger(replace(SETTINGS, audit_store=tmp_path / "audit.jsonl", audit_anchor_url="https://anchor.example/ingest", audit_anchor_token="t0k"))
    record = audit.append(tool="logs", action="infra.logs.read", risk_tier="low", outcome="success", request={"q": "secret-input"})
    assert sent and sent[0][0] == "https://anchor.example/ingest"
    body = sent[0][1]["json"]
    assert body["event_hash"] == record["event_hash"]
    assert "secret-input" not in str(body)
    assert sent[0][1]["headers"]["Authorization"] == "Bearer t0k"


class _InlineThread:
    def __init__(self, target, **_):
        self.target = target

    def start(self):
        self.target()
