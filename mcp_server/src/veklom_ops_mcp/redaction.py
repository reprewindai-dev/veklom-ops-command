from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_KEY = re.compile(
    r"(?ix)"
    r"(^|[_-])(" 
    r"password|passwd|pwd|secret|token|access[_-]?token|refresh[_-]?token|"
    r"api[_-]?key|private[_-]?key|signing[_-]?key|authorization|cookie|"
    r"client[_-]?secret|webhook[_-]?secret|real[_-]?value"
    r")($|[_-])"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
_KV_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|authorization)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_URI_CREDENTIALS = re.compile(
    r"(?i)([a-z][a-z0-9+.-]*://[^:\s/@]+:)([^@\s/]+)(@)"
)
_ENV_SECRET = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|DATABASE_URL|REDIS_URL|DSN)[A-Z0-9_]*)=([^\s]+)"
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_PEM = re.compile(
    r"-----BEGIN [A-Z0-9 ]*(?:PRIVATE KEY|SECRET)[A-Z0-9 ]*-----.*?"
    r"-----END [A-Z0-9 ]*(?:PRIVATE KEY|SECRET)[A-Z0-9 ]*-----",
    re.DOTALL,
)


def is_sensitive_key(key: str) -> bool:
    return bool(_SENSITIVE_KEY.search(key))


def redact_text(value: str, max_chars: int | None = None) -> str:
    value = _PEM.sub(REDACTED, value)
    value = _BEARER.sub(f"Bearer {REDACTED}", value)
    value = _JWT.sub(REDACTED, value)
    value = _ENV_SECRET.sub(lambda m: f"{m.group(1)}={REDACTED}", value)
    value = _URI_CREDENTIALS.sub(lambda m: f"{m.group(1)}{REDACTED}{m.group(3)}", value)
    value = _KV_SECRET.sub(lambda m: f"{m.group(1)}={REDACTED}", value)
    if max_chars is not None and len(value) > max_chars:
        return value[:max_chars] + "\n…[TRUNCATED]"
    return value


def redact(value: Any, *, max_chars: int | None = None) -> Any:
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if is_sensitive_key(key):
                output[key] = REDACTED
            else:
                output[key] = redact(raw_value, max_chars=max_chars)
        return output

    if isinstance(value, str):
        return redact_text(value, max_chars=max_chars)

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact(item, max_chars=max_chars) for item in value]

    return value
