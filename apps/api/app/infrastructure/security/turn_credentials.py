"""Ephemeral TURN credentials (coturn use-auth-secret / REST style)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from datetime import UTC, datetime
from typing import Any


DEFAULT_TURN_SECRET = "dev_turn_secret_change_me"
DEFAULT_TTL = 300


def resolve_turn_secret() -> str:
    return os.environ.get("TURN_SECRET") or DEFAULT_TURN_SECRET


def resolve_turn_host() -> str:
    return os.environ.get("TURN_HOST") or "127.0.0.1"


def resolve_turn_port() -> int:
    raw = os.environ.get("TURN_PORT") or "3478"
    return int(raw)


def resolve_turn_ttl() -> int:
    raw = os.environ.get("TURN_TTL_SECONDS") or str(DEFAULT_TTL)
    ttl = int(raw)
    if ttl < 30:
        raise ValueError("TURN_TTL_SECONDS must be >= 30")
    return ttl


def issue_turn_credentials(
    *,
    match_id: str,
    now: float | None = None,
    ttl: int | None = None,
    secret: str | None = None,
    host: str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """
    Coturn static-auth-secret credential:
      username = "<unix_expiry>:<match_id>"
      credential = base64(hmac_sha1(secret, username))
    """
    clock = now if now is not None else time.time()
    lifetime = ttl if ttl is not None else resolve_turn_ttl()
    expiry = int(clock) + lifetime
    username = f"{expiry}:{match_id}"
    key = (secret or resolve_turn_secret()).encode("utf-8")
    digest = hmac.new(key, username.encode("utf-8"), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode("ascii")
    turn_host = host or resolve_turn_host()
    turn_port = port if port is not None else resolve_turn_port()
    urls = [
        f"turn:{turn_host}:{turn_port}?transport=udp",
        f"turn:{turn_host}:{turn_port}?transport=tcp",
    ]
    return {
        "urls": urls,
        "username": username,
        "credential": credential,
        "ttl": lifetime,
        "expires_at": datetime.fromtimestamp(expiry, tz=UTC).isoformat(),
    }


def credentials_expired(username: str, *, now: float | None = None) -> bool:
    """True if username expiry prefix is in the past."""
    try:
        expiry_s, _rest = username.split(":", 1)
        expiry = int(expiry_s)
    except (ValueError, AttributeError):
        return True
    clock = now if now is not None else time.time()
    return clock >= expiry
