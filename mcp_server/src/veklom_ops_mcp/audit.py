from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

import httpx
from filelock import FileLock

from .approval import canonical_json
from .config import SETTINGS, Settings

GENESIS = "0" * 64


def _hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class AuditLedger:
    """Hash-chained, metadata-only ledger.

    The chain alone proves edits in the middle. Deleting the newest events or replacing the whole
    file is only detectable against a head recorded somewhere else, so every event hash can be
    pushed to VEKLOM_MCP_AUDIT_ANCHOR_URL and verify() accepts a previously recorded anchor head.
    """

    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    @property
    def path(self) -> Path:
        return self.settings.audit_store

    def append(
        self,
        *,
        tool: str,
        action: str,
        risk_tier: str,
        outcome: str,
        request: dict[str, Any],
        result: Any = None,
        approved_by: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        path = self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        # Serialize read-last-hash + append so concurrent workers cannot fork the chain.
        with FileLock(str(path) + ".lock", timeout=5):
            previous = self._last_hash()
            event = {
                "v": 1,
                "timestamp": int(time.time()),
                "tool": tool,
                "action": action,
                "risk_tier": risk_tier,
                "outcome": outcome,
                "request_sha256": _hash(request),
                "result_sha256": _hash(result),
                "approved_by": approved_by,
                "reason": reason,
                "previous_hash": previous,
            }
            event_hash = _hash(event)
            record = {**event, "event_hash": event_hash}
            with path.open("a", encoding="utf-8") as fh:
                fh.write(canonical_json(record) + "\n")
        self._anchor(record)
        return record

    def _anchor(self, record: dict[str, Any]) -> None:
        url = self.settings.audit_anchor_url
        if not url:
            return
        body = {
            "event_hash": record["event_hash"],
            "previous_hash": record["previous_hash"],
            "timestamp": record["timestamp"],
            "outcome": record["outcome"],
            "risk_tier": record["risk_tier"],
            "audience": self.settings.approval_audience,
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.audit_anchor_token:
            headers["Authorization"] = f"Bearer {self.settings.audit_anchor_token}"

        def post() -> None:
            try:
                httpx.post(url, json=body, headers=headers, timeout=3.0, follow_redirects=False)
            except httpx.HTTPError:
                # The local chain is still authoritative; a missing anchor is visible as a gap off-box.
                pass

        threading.Thread(target=post, name="audit-anchor", daemon=True).start()

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = line
        if not last:
            return GENESIS
        try:
            return str(json.loads(last)["event_hash"])
        except (json.JSONDecodeError, KeyError):
            return "CORRUPT"

    def head(self) -> dict[str, Any]:
        """Current head, for an external system to record as a future anchor."""
        result = self.verify()
        return {"head": result.get("head"), "events": result.get("events"), "valid": result.get("valid")}

    def verify(self, anchor_head: str | None = None) -> dict[str, Any]:
        """Verify the chain; with anchor_head, also prove that previously recorded head is still in it."""
        if not self.path.exists():
            if anchor_head and anchor_head != GENESIS:
                return {"valid": False, "events": 0, "reason": "anchor_not_found"}
            return {"valid": True, "events": 0, "head": GENESIS}
        previous = GENESIS
        count = 0
        anchor_seen = anchor_head is None or anchor_head == GENESIS
        for number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                event_hash = record.pop("event_hash")
            except (json.JSONDecodeError, KeyError):
                return {"valid": False, "events": count, "bad_line": number, "reason": "malformed_record"}
            if record.get("previous_hash") != previous:
                return {"valid": False, "events": count, "bad_line": number, "reason": "previous_hash_mismatch"}
            calculated = _hash(record)
            if calculated != event_hash:
                return {"valid": False, "events": count, "bad_line": number, "reason": "event_hash_mismatch"}
            previous = event_hash
            count += 1
            if event_hash == anchor_head:
                anchor_seen = True
        if not anchor_seen:
            return {"valid": False, "events": count, "head": previous, "reason": "anchor_not_found"}
        return {"valid": True, "events": count, "head": previous, "anchored": anchor_head is not None}

    def tail(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows: list[dict[str, Any]] = []
        for line in lines[-max(1, min(limit, 200)):]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"corrupt": True})
        return rows
