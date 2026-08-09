from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any

from filelock import FileLock

from .config import SETTINGS, Settings


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def params_hash(params: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(params).encode()).hexdigest()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class ApprovalClaims:
    v: int
    nonce: str
    action: str
    params_sha256: str
    approved_by: str
    issued_at: int
    expires_at: int


class ApprovalError(RuntimeError):
    pass


class ApprovalAuthority:
    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    def _key(self) -> bytes:
        raw = self.settings.approval_hmac_key
        if not raw:
            raise ApprovalError("Approval authority is not configured.")
        key = raw.encode()
        if len(key) < 32:
            raise ApprovalError("Approval authority key must be at least 32 bytes.")
        return key

    def issue(self, action: str, params: dict[str, Any], approved_by: str, ttl_seconds: int | None = None) -> str:
        if not action or not approved_by:
            raise ApprovalError("Action and approver identity are required.")
        ttl = min(ttl_seconds or self.settings.approval_ttl_seconds, self.settings.approval_ttl_seconds)
        if ttl < 1:
            raise ApprovalError("Approval TTL must be positive.")
        now = int(time.time())
        claims = ApprovalClaims(
            v=1,
            nonce=secrets.token_urlsafe(18),
            action=action,
            params_sha256=params_hash(params),
            approved_by=approved_by,
            issued_at=now,
            expires_at=now + ttl,
        )
        payload = canonical_json(asdict(claims)).encode()
        signature = hmac.new(self._key(), payload, hashlib.sha256).digest()
        return f"v1.{_b64encode(payload)}.{_b64encode(signature)}"

    def verify_and_consume(self, token: str, action: str, params: dict[str, Any]) -> ApprovalClaims:
        try:
            version, payload_b64, sig_b64 = token.split(".", 2)
            payload = _b64decode(payload_b64)
            supplied_sig = _b64decode(sig_b64)
        except (ValueError, base64.binascii.Error) as exc:
            raise ApprovalError("Malformed approval token.") from exc
        if version != "v1":
            raise ApprovalError("Unsupported approval token version.")
        expected = hmac.new(self._key(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, supplied_sig):
            raise ApprovalError("Approval signature is invalid.")
        try:
            claims = ApprovalClaims(**json.loads(payload))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ApprovalError("Approval payload is invalid.") from exc
        now = int(time.time())
        if claims.expires_at < now:
            raise ApprovalError("Approval token expired.")
        if claims.issued_at > now + 30:
            raise ApprovalError("Approval token issued in the future.")
        if claims.action != action:
            raise ApprovalError("Approval token is bound to a different action.")
        if not hmac.compare_digest(claims.params_sha256, params_hash(params)):
            raise ApprovalError("Approval token is bound to different parameters.")
        self._consume_nonce(claims.nonce, claims.expires_at)
        return claims

    def _consume_nonce(self, nonce: str, expires_at: int) -> None:
        path = self.settings.approval_store
        path.parent.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        with FileLock(str(path) + ".lock", timeout=5):
            seen: set[str] = set()
            retained: list[dict[str, Any]] = []
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if int(row.get("expires_at", 0)) >= now:
                        retained.append(row)
                        seen.add(str(row.get("nonce", "")))
            if nonce in seen:
                raise ApprovalError("Approval token has already been consumed.")
            retained.append({"nonce": nonce, "expires_at": expires_at})
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text("".join(canonical_json(row) + "\n" for row in retained), encoding="utf-8")
            temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint a one-time Veklom MCP approval token outside ChatGPT.")
    parser.add_argument("--action", required=True)
    parser.add_argument("--params-json", required=True, help="Exact JSON object the approved action will receive.")
    parser.add_argument("--approved-by", required=True, help="Human or separately trusted coding-agent identity.")
    parser.add_argument("--ttl", type=int, default=None)
    args = parser.parse_args()
    settings = Settings.from_env()
    if not settings.approval_hmac_key:
        raise SystemExit("VEKLOM_MCP_APPROVAL_HMAC_KEY is required to mint approvals")
    params = json.loads(args.params_json)
    if not isinstance(params, dict):
        raise SystemExit("--params-json must decode to a JSON object")
    token = ApprovalAuthority(settings).issue(args.action, params, args.approved_by, args.ttl)
    print(token)


if __name__ == "__main__":
    main()
