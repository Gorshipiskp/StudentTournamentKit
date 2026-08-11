"""HMAC for CS2 webhooks — ARCHITECTURE §15.3 / CONTRACT §2."""

from __future__ import annotations

import hashlib
import hmac
import os


def sign_body(secret: str, raw_body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, raw_body: bytes, header_value: str | None) -> bool:
    if not header_value:
        return False
    expected = sign_body(secret, raw_body)
    return hmac.compare_digest(expected, header_value.strip())


def resolve_webhook_secret(match_secret: str | None) -> str | None:
    if match_secret:
        return match_secret
    return os.environ.get("CS2_WEBHOOK_SECRET") or os.environ.get(
        "FAKE_CS2_WEBHOOK_SECRET"
    )
