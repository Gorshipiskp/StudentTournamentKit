"""HMAC-signed invite session tokens (short-lived, capability-scoped)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.identity.entities import InviteSession

DEFAULT_DEV_SECRET = "dev_session_secret_change_me"
SESSION_TTL_DEFAULT = timedelta(hours=8)
_PREFIX = "stk1"


def resolve_session_secret() -> str:
    return os.environ.get("STK_SESSION_SECRET") or DEFAULT_DEV_SECRET


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def issue_session_token(
    session: InviteSession,
    *,
    secret: str | None = None,
) -> str:
    payload: dict[str, Any] = {
        "iid": session.invite_id,
        "mid": session.match_id,
        "role": session.role,
        "caps": sorted(session.caps),
        "exp": int(session.expires_at.timestamp()),
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    key = (secret or resolve_session_secret()).encode("utf-8")
    sig = _b64url_encode(hmac.new(key, body.encode("ascii"), hashlib.sha256).digest())
    return f"{_PREFIX}.{body}.{sig}"


def parse_session_token(
    token: str,
    *,
    secret: str | None = None,
    now: datetime | None = None,
) -> InviteSession:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != _PREFIX:
        raise ValueError("invalid session token")
    _, body, sig = parts
    key = (secret or resolve_session_secret()).encode("utf-8")
    expected = _b64url_encode(hmac.new(key, body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid session signature")
    try:
        payload = json.loads(_b64url_decode(body))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid session payload") from exc
    exp_ts = int(payload["exp"])
    expires_at = datetime.fromtimestamp(exp_ts, tz=UTC)
    clock = now or datetime.now(UTC)
    if clock >= expires_at:
        raise ValueError("session expired")
    caps = frozenset(str(c) for c in payload["caps"])
    return InviteSession(
        invite_id=str(payload["iid"]),
        match_id=str(payload["mid"]),
        role=str(payload["role"]),
        caps=caps,
        expires_at=expires_at,
    )


def default_session_expiry(*, now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + SESSION_TTL_DEFAULT
