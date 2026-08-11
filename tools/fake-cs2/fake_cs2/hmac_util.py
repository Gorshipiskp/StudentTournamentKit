"""HMAC helpers — match infra/game-server/CONTRACT.md §2."""

from __future__ import annotations

import hashlib
import hmac


def sign_body(secret: str, raw_body: bytes) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, raw_body: bytes, header_value: str) -> bool:
    expected = sign_body(secret, raw_body)
    return hmac.compare_digest(expected, header_value.strip())
