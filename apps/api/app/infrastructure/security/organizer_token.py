"""HMAC-signed organizer session tokens (env bootstrap login)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.identity.organizer import ROLE_ORGANIZER, OrganizerSession
from app.infrastructure.security.session_token import resolve_session_secret

DEFAULT_DEV_PASSWORD = "changeme_organizer"
DEFAULT_DEV_USERNAME = "organizer"
ORGANIZER_TTL_DEFAULT = timedelta(hours=12)
_PREFIX = "stkorg1"


def resolve_organizer_username() -> str:
    return os.environ.get("STK_ORGANIZER_USERNAME") or DEFAULT_DEV_USERNAME


def resolve_organizer_password() -> str:
    return os.environ.get("STK_ORGANIZER_PASSWORD") or DEFAULT_DEV_PASSWORD


def verify_organizer_credentials(username: str, password: str) -> bool:
    expected_user = resolve_organizer_username()
    expected_pass = resolve_organizer_password()
    user_ok = hmac.compare_digest(username.strip(), expected_user)
    pass_ok = hmac.compare_digest(password, expected_pass)
    return user_ok and pass_ok


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def issue_organizer_token(
    *,
    secret: str | None = None,
    now: datetime | None = None,
    ttl: timedelta | None = None,
) -> tuple[str, OrganizerSession]:
    clock = now or datetime.now(UTC)
    expires_at = clock + (ttl or ORGANIZER_TTL_DEFAULT)
    session = OrganizerSession(role=ROLE_ORGANIZER, expires_at=expires_at)
    payload: dict[str, Any] = {
        "role": session.role,
        "exp": int(session.expires_at.timestamp()),
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    key = (secret or resolve_session_secret()).encode("utf-8")
    sig = _b64url_encode(hmac.new(key, body.encode("ascii"), hashlib.sha256).digest())
    return f"{_PREFIX}.{body}.{sig}", session


def parse_organizer_token(
    token: str,
    *,
    secret: str | None = None,
    now: datetime | None = None,
) -> OrganizerSession:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != _PREFIX:
        raise ValueError("invalid organizer token")
    _, body, sig = parts
    key = (secret or resolve_session_secret()).encode("utf-8")
    expected = _b64url_encode(hmac.new(key, body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid organizer signature")
    try:
        payload = json.loads(_b64url_decode(body))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid organizer payload") from exc
    role = str(payload.get("role") or "")
    if role != ROLE_ORGANIZER:
        raise ValueError("not an organizer token")
    exp_ts = int(payload["exp"])
    expires_at = datetime.fromtimestamp(exp_ts, tz=UTC)
    clock = now or datetime.now(UTC)
    if clock >= expires_at:
        raise ValueError("organizer session expired")
    return OrganizerSession(role=role, expires_at=expires_at)
