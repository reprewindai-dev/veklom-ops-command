from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .approval import canonical_json
from .config import SETTINGS, Settings

GENESIS = "0" * 64


def _hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class AuditLedger:
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
        return record

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

    def verify(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"valid": True, "events": 0, "head": GENESIS}
        previous = GENESIS
        count = 0
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
        return {"valid": True, "events": count, "head": previous}

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
