from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from filelock import FileLock

from .config import SETTINGS, Settings

TOKEN_VERSION = "v2"


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
    """Everything an approval is bound to. A token is valid for exactly one (aud, tool, action, params) call."""

    v: int
    nonce: str
    aud: str
    tool: str
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

    def issue(
        self,
        *,
        audience: str,
        tool: str,
        action: str,
        params: dict[str, Any],
        approved_by: str,
        ttl_seconds: int | None = None,
    ) -> str:
        if not audience or not tool or not action or not approved_by:
            raise ApprovalError("Audience, tool, action and approver identity are required.")
        ttl = min(ttl_seconds or self.max_ttl_seconds, self.max_ttl_seconds)
        if ttl < 1:
            raise ApprovalError("Approval TTL must be positive.")
        now = int(time.time())
        claims = ApprovalClaims(
            v=2,
            nonce=secrets.token_urlsafe(18),
            aud=audience,
            tool=tool,
            action=action,
            params_sha256=params_hash(params),
            approved_by=approved_by,
            issued_at=now,
            expires_at=now + ttl,
        )
        payload = canonical_json(asdict(claims)).encode()
        signature = self.private_key.sign(payload)
        return f"{TOKEN_VERSION}.{_b64encode(payload)}.{_b64encode(signature)}"


class ApprovalAuthority:
    """MCP-side verifier. It possesses only the public key and cannot mint approvals."""

    def __init__(self, settings: Settings = SETTINGS):
        self.settings = settings

    def _public_keys(self) -> list[Ed25519PublicKey]:
        """Every trusted approver key. Comma-separated, so several devices or people can each approve."""
        configured = [item.strip() for item in (self.settings.approval_public_key_b64 or "").split(",") if item.strip()]
        if not configured:
            raise ApprovalError("Approval verifier public key is not configured.")
        keys = []
        for raw_b64 in configured:
            raw = _b64decode(raw_b64)
            if len(raw) != 32:
                raise ApprovalError("Ed25519 approval public key must be exactly 32 raw bytes.")
            keys.append(Ed25519PublicKey.from_public_bytes(raw))
        return keys

    def _verify_signature(self, signature: bytes, payload: bytes) -> None:
        for key in self._public_keys():
            try:
                key.verify(signature, payload)
                return
            except InvalidSignature:
                continue
        raise InvalidSignature()

    def verify_and_consume(self, token: str, *, tool: str, action: str, params: dict[str, Any]) -> ApprovalClaims:
        claims = self.verify_signed(token)
        if claims.tool != tool:
            raise ApprovalError("Approval token is bound to a different tool.")
        if claims.action != action:
            raise ApprovalError("Approval token is bound to a different action.")
        if not hmac.compare_digest(claims.params_sha256, params_hash(params)):
            raise ApprovalError("Approval token is bound to different parameters.")
        self._consume_nonce(claims.nonce, claims.expires_at)
        return claims

    def verify_signed(self, token: str) -> ApprovalClaims:
        """Signature, version, time and audience checks only. Does not bind to a call or consume the nonce."""
        audience = self.settings.approval_audience
        if not audience:
            raise ApprovalError("Approval audience is not configured; approvals cannot be verified.")
        if len(token) > 4096:
            raise ApprovalError("Approval token is too large.")
        try:
            version, payload_b64, sig_b64 = token.split(".", 2)
            payload = _b64decode(payload_b64)
            supplied_sig = _b64decode(sig_b64)
        except ValueError as exc:
            raise ApprovalError("Malformed approval token.") from exc
        if version != TOKEN_VERSION:
            raise ApprovalError("Unsupported approval token version; mint a v2 (audience-bound) approval.")
        try:
            self._verify_signature(supplied_sig, payload)
        except InvalidSignature as exc:
            raise ApprovalError("Approval signature is invalid.") from exc
        try:
            claims = ApprovalClaims(**json.loads(payload))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ApprovalError("Approval payload is invalid.") from exc
        now = int(time.time())
        if claims.v != 2:
            raise ApprovalError("Unsupported approval claims version.")
        if claims.expires_at < now:
            raise ApprovalError("Approval token expired.")
        if claims.expires_at - claims.issued_at > self.settings.approval_ttl_seconds:
            raise ApprovalError("Approval token TTL exceeds server policy.")
        if claims.issued_at > now + 30:
            raise ApprovalError("Approval token issued in the future.")
        if not hmac.compare_digest(claims.aud, audience):
            raise ApprovalError("Approval token is bound to a different deployment (audience).")
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


def request_id(*, audience: str, tool: str, action: str, params_sha256: str) -> str:
    """Deterministic id of one exact call. A delivered approval can only ever match the call it was signed for."""
    return hashlib.sha256(canonical_json([audience, tool, action, params_sha256]).encode()).hexdigest()[:32]


def build_approval_request(
    *,
    audience: str,
    tool: str,
    action: str,
    params: dict[str, Any],
    ttl_seconds: int,
    risk_tier: str | None = None,
    reason: str | None = None,
    approver_url: str | None = None,
    deliver_url: str | None = None,
) -> dict[str, Any]:
    """What the agent relays to a human. Every approver re-hashes params, so the agent cannot swap them."""
    digest = params_hash(params)
    rid = request_id(audience=audience, tool=tool, action=action, params_sha256=digest)
    request: dict[str, Any] = {
        "request_id": rid,
        "aud": audience,
        "tool": tool,
        "action": action,
        "params": params,
        "params_sha256": digest,
        "risk_tier": risk_tier,
        "reason": reason,
        "expires_after_seconds": ttl_seconds,
    }
    if deliver_url:
        request["deliver_to"] = deliver_url
    if approver_url:
        fragment = _b64encode(canonical_json(request).encode())
        request["approve_url"] = f"{approver_url.split('#', 1)[0]}#r={fragment}"
        request["how_to_approve"] = (
            "Show the human approve_url. They review the exact call on their own device and approve it once. "
            "Then call wait_for_approval with request_id and, once approved, repeat this exact tool call."
        )
    else:
        request["how_to_approve"] = (
            "A human (or separately trusted environment holding the approval private key) runs: "
            "veklom-mcp-approve --approved-by <you> --request-json '<this approval_request object>' "
            "and returns the printed token to the agent as approval_token."
        )
    return request


class ApprovalInbox:
    """Approvals delivered by an approver device, waiting for the agent to repeat the exact call.

    Holding a token here grants nothing by itself: it is still fully verified and its nonce consumed
    when the matching call runs. Entries expire with their token and the inbox is bounded.
    """

    MAX_ENTRIES = 500

    def __init__(self, settings: Settings = SETTINGS, authority: ApprovalAuthority | None = None):
        self.settings = settings
        self.authority = authority or ApprovalAuthority(settings)

    @property
    def path(self):
        return self.settings.approval_store.with_name("delivered.jsonl")

    def _rows(self, now: int) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(row.get("expires_at", 0)) >= now:
                rows.append(row)
        return rows

    def _write(self, rows: list[dict[str, Any]]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")
        temporary.replace(self.path)

    def deliver(self, token: str) -> dict[str, Any]:
        claims = self.authority.verify_signed(token)
        rid = request_id(audience=claims.aud, tool=claims.tool, action=claims.action, params_sha256=claims.params_sha256)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        with FileLock(str(self.path) + ".lock", timeout=5):
            rows = [row for row in self._rows(now) if row.get("request_id") != rid]
            if len(rows) >= self.MAX_ENTRIES:
                raise ApprovalError("Approval inbox is full.")
            rows.append({"request_id": rid, "token": token, "expires_at": claims.expires_at, "approved_by": claims.approved_by})
            self._write(rows)
        return {"delivered": True, "request_id": rid, "approved_by": claims.approved_by, "expires_at": claims.expires_at}

    def take(self, rid: str) -> str | None:
        if not self.path.exists():
            return None
        now = int(time.time())
        with FileLock(str(self.path) + ".lock", timeout=5):
            rows = self._rows(now)
            match = next((row for row in rows if row.get("request_id") == rid), None)
            if match is None:
                return None
            self._write([row for row in rows if row is not match])
        return str(match["token"])

    def status(self, rid: str) -> dict[str, Any]:
        now = int(time.time())
        row = next((row for row in self._rows(now) if row.get("request_id") == rid), None)
        if row is None:
            return {"request_id": rid, "state": "waiting"}
        return {"request_id": rid, "state": "approved", "approved_by": row.get("approved_by"), "expires_at": row.get("expires_at")}


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


def resolve_request(args: argparse.Namespace, pinned_audiences: list[str]) -> tuple[str, str, str, dict[str, Any]]:
    """Return (audience, tool, action, params) from either a relayed approval_request or explicit flags."""
    if args.request_json:
        try:
            request = json.loads(args.request_json)
        except json.JSONDecodeError as exc:
            raise ApprovalError("--request-json is not valid JSON.") from exc
        if isinstance(request, dict) and isinstance(request.get("approval_request"), dict):
            request = request["approval_request"]
        if not isinstance(request, dict):
            raise ApprovalError("--request-json must be the approval_request object returned by the MCP.")
        audience, tool, action, params = request.get("aud"), request.get("tool"), request.get("action"), request.get("params")
        if not all(isinstance(value, str) and value for value in (audience, tool, action)) or not isinstance(params, dict):
            raise ApprovalError("approval_request must contain aud, tool, action and a params object.")
        claimed = request.get("params_sha256")
        if claimed is not None and claimed != params_hash(params):
            raise ApprovalError("approval_request params_sha256 does not match its params; refusing to sign.")
    else:
        if not (args.tool and args.action and args.params_json):
            raise ApprovalError("Provide --request-json, or all of --tool, --action and --params-json.")
        tool, action = args.tool, args.action
        params = json.loads(args.params_json)
        if not isinstance(params, dict):
            raise ApprovalError("--params-json must decode to a JSON object.")
        audience = args.audience or (pinned_audiences[0] if len(pinned_audiences) == 1 else None)
        if not audience:
            raise ApprovalError("--audience is required (or pin exactly one in VEKLOM_MCP_APPROVER_AUDIENCES).")
    if args.audience and args.audience != audience:
        raise ApprovalError(f"Request targets audience {audience!r}, but --audience is {args.audience!r}.")
    if pinned_audiences and audience not in pinned_audiences:
        raise ApprovalError(f"Audience {audience!r} is not in VEKLOM_MCP_APPROVER_AUDIENCES; refusing to sign.")
    return audience, tool, action, params


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Mint a one-time Ed25519 approval for exactly one MCP call, outside the agent.")
    parser.add_argument("--request-json", help="The approval_request object the MCP returned to the agent.")
    parser.add_argument("--tool")
    parser.add_argument("--action")
    parser.add_argument("--params-json", help="Exact JSON object the approved tool call will receive.")
    parser.add_argument("--audience", help="Deployment identity (VEKLOM_MCP_APPROVAL_AUDIENCE on the target server).")
    parser.add_argument("--approved-by", required=True, help="Human or separately trusted coding-agent identity.")
    parser.add_argument("--ttl", type=int, default=None)
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation.")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    private_key = os.getenv("VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64")
    if not private_key:
        raise SystemExit("VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64 is required in the external approval environment")
    pinned = [item.strip() for item in os.getenv("VEKLOM_MCP_APPROVER_AUDIENCES", "").split(",") if item.strip()]
    try:
        audience, tool, action, params = resolve_request(args, pinned)
    except ApprovalError as exc:
        raise SystemExit(f"refused: {exc}") from exc

    print("You are approving exactly one call:", file=sys.stderr)
    print(f"  deployment : {audience}{'' if pinned else '   (unpinned: set VEKLOM_MCP_APPROVER_AUDIENCES)'}", file=sys.stderr)
    print(f"  tool       : {tool}", file=sys.stderr)
    print(f"  action     : {action}", file=sys.stderr)
    print(f"  params     : {canonical_json(params)}", file=sys.stderr)
    if not args.yes:
        if not sys.stdin.isatty():
            raise SystemExit("refused: confirmation needs a terminal; pass --yes only from a trusted script")
        if input("Approve? [y/N] ").strip().lower() not in {"y", "yes"}:
            raise SystemExit("not approved")

    token = ApprovalSigner(private_key, max_ttl_seconds=settings.approval_ttl_seconds).issue(
        audience=audience, tool=tool, action=action, params=params, approved_by=args.approved_by, ttl_seconds=args.ttl
    )
    print(token)


def keygen_main() -> None:
    public_key, private_key = generate_keypair()
    print("# Store PUBLIC on the MCP server; keep PRIVATE outside the MCP server.")
    print(f"VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64={public_key}")
    print(f"VEKLOM_MCP_APPROVAL_PRIVATE_KEY_B64={private_key}")


if __name__ == "__main__":
    main()
