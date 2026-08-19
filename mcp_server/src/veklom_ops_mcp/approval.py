from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from filelock import FileLock

from .config import SETTINGS, Settings


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def params_hash(params: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(params).encode()).hexdigest()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ApprovalError("Invalid base64 approval material.") from exc


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


class ApprovalSigner:
    """External approval signer. This class is not instantiated by the MCP server."""

    def __init__(self, private_key_b64: str, *, max_ttl_seconds: int = 600):
        raw = _b64decode(private_key_b64)
        if len(raw) != 32:
            raise ApprovalError("Ed25519 approval private key must be exactly 32 raw bytes.")
        self.private_key = Ed25519PrivateKey.from_private_bytes(raw)
        self.max_ttl_seconds = max(1, min(max_ttl_seconds, 3600))

    def issue(self, action: str, params: dict[str, Any], approved_by: str, ttl_seconds: int | None = None) -> str:
        if not action or not approved_by:
            raise ApprovalError("Action and approver identity are required.")
        ttl = min(ttl_seconds or self.max_ttl_seconds, self.max_ttl_seconds)
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
        signature = self.private_key.sign(payload)
        return f"v1.{_b64encode(payload)}.{_b64encode(signature)}"


class ApprovalAuthority:
    """MCP-side verifier. It possesses only the public key and cannot mint approvals."""

    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    def _public_key(self) -> Ed25519PublicKey:
        raw_b64 = self.settings.approval_public_key_b64
        if not raw_b64:
            raise ApprovalError("Approval verifier public key is not configured.")
        raw = _b64decode(raw_b64)
        if len(raw) != 32:
            raise ApprovalError("Ed25519 approval public key must be exactly 32 raw bytes.")
        return Ed25519PublicKey.from_public_bytes(raw)

    def verify_and_consume(self, token: str, action: str, params: dict[str, Any]) -> ApprovalClaims:
        try:
            version, payload_b64, sig_b64 = token.split(".", 2)
            payload = _b64decode(payload_b64)
            supplied_sig = _b64decode(sig_b64)
        except ValueError as exc:
            raise ApprovalError("Malformed approval token.") from exc
        if version != "v1":
            raise ApprovalError("Unsupported approval token version.")
        try:
            self._public_key().verify(supplied_sig, payload)
        except InvalidSignature as exc:
            raise ApprovalError("Approval signature is invalid.") from exc
        try:
            claims = ApprovalClaims(**json.loads(payload))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ApprovalError("Approval payload is invalid.") from exc
        now = int(time.time())
        if claims.v != 1:
            raise ApprovalError("Unsupported approval claims version.")
        if claims.expires_at < now:
            raise ApprovalError("Approval token expired.")
        if claims.expires_at - claims.issued_at > self.settings.approval_ttl_seconds:
            raise ApprovalError("Approval token TTL exceeds server policy.")
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


def generate_keypair() -> tuple[str, str]:
    """Return (public_b64, private_b64) using raw Ed25519 key material."""
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64encode(public_raw), _b64encode(private_raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint a one-time Ed25519 Veklom MCP approval outside ChatGPT.")
    parser.add_argument("--action", required=True)
    parser.add_argument("--params-json", required=True, help="Exact JSON object the approved action will receive.")
    parser.add_argument("--approved-by", required=True, help="Human or separately trusted coding-agent identity.")
    parser.add_argument("--ttl", type=int, default=None)
    args = parser.parse_args()
    settings = Settings.from_env()
    private_key = os.getenv("VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64")
    if not private_key:
        raise SystemExit("VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64 is required in the external approval environment")
    params = json.loads(args.params_json)
    if not isinstance(params, dict):
        raise SystemExit("--params-json must decode to a JSON object")
    token = ApprovalSigner(private_key, max_ttl_seconds=settings.approval_ttl_seconds).issue(
        args.action, params, args.approved_by, args.ttl
    )
    print(token)


def keygen_main() -> None:
    public_key, private_key = generate_keypair()
    print("# Store PUBLIC on the MCP server; keep PRIVATE outside the MCP server.")
    print(f"VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64={public_key}")
    print(f"VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64={private_key}")


if __name__ == "__main__":
    main()
