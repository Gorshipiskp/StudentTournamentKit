"""Ephemeral MediaMTX WHIP/WHEP bearer tokens (HMAC; MediaMTX authHTTP)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import UTC, datetime
from typing import Any, Literal

Action = Literal["publish", "read"]

_PREFIX = "mtx"
DEFAULT_TTL = 600
DEFAULT_SECRET = "dev_mediamtx_auth_secret_change_me"
MAX_WHEP_PER_MATCH = 2


def resolve_mediamtx_public_url() -> str:
    return (os.environ.get("MEDIAMTX_PUBLIC_URL") or "http://127.0.0.1:8889").rstrip(
        "/"
    )


def resolve_mediamtx_auth_secret() -> str:
    return (
        os.environ.get("MEDIAMTX_AUTH_SECRET")
        or os.environ.get("STK_SESSION_SECRET")
        or DEFAULT_SECRET
    )


def resolve_mediamtx_credential_ttl() -> int:
    raw = os.environ.get("MEDIAMTX_CREDENTIAL_TTL_SECONDS") or str(DEFAULT_TTL)
    ttl = int(raw)
    if ttl < 60:
        raise ValueError("MEDIAMTX_CREDENTIAL_TTL_SECONDS must be >= 60")
    return ttl


def mediamtx_path(match_id: str) -> str:
    return f"stk/{match_id}"


def whip_url(match_id: str, *, base: str | None = None) -> str:
    root = (base or resolve_mediamtx_public_url()).rstrip("/")
    return f"{root}/{mediamtx_path(match_id)}/whip"


def whep_url(match_id: str, *, base: str | None = None) -> str:
    root = (base or resolve_mediamtx_public_url()).rstrip("/")
    return f"{root}/{mediamtx_path(match_id)}/whep"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _sign(body: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).digest()
    return _b64url(digest)


def issue_mediamtx_bearer(
    *,
    match_id: str,
    action: Action,
    now: float | None = None,
    ttl: int | None = None,
    secret: str | None = None,
    jti: str | None = None,
) -> dict[str, Any]:
    """
    Issue bearer for OBS WHIP (publish) or /watch WHEP (read).

    Token: mtx.<payload_b64>.<sig>
    Payload: {v, act, path, exp, jti}
    Never log the bearer.
    """
    clock = now if now is not None else time.time()
    lifetime = ttl if ttl is not None else resolve_mediamtx_credential_ttl()
    expiry = int(clock) + lifetime
    path = mediamtx_path(match_id)
    token_id = jti or secrets.token_hex(8)
    payload = {
        "v": 1,
        "act": action,
        "path": path,
        "exp": expiry,
        "jti": token_id,
    }
    body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    key = secret or resolve_mediamtx_auth_secret()
    sig = _sign(body, key)
    bearer = f"{_PREFIX}.{body}.{sig}"
    expires_at = datetime.fromtimestamp(expiry, tz=UTC).isoformat()
    out: dict[str, Any] = {
        "path": path,
        "bearer": bearer,
        "ttl": lifetime,
        "expires_at": expires_at,
        "jti": token_id,
    }
    if action == "publish":
        out["whip_url"] = whip_url(match_id)
    else:
        out["whep_url"] = whep_url(match_id)
    return out


def parse_mediamtx_bearer(
    token: str,
    *,
    now: float | None = None,
    secret: str | None = None,
) -> dict[str, Any]:
    """Validate bearer; raise ValueError on failure. Does not log token."""
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != _PREFIX:
        raise ValueError("invalid mediamtx bearer")
    _pfx, body, sig = parts
    key = secret or resolve_mediamtx_auth_secret()
    expected = _sign(body, key)
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid mediamtx bearer signature")
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid mediamtx bearer payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid mediamtx bearer payload")
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("invalid mediamtx bearer exp")
    clock = now if now is not None else time.time()
    if clock >= exp:
        raise ValueError("mediamtx bearer expired")
    act = payload.get("act")
    path = payload.get("path")
    jti = payload.get("jti")
    if act not in ("publish", "read") or not isinstance(path, str) or not path:
        raise ValueError("invalid mediamtx bearer claims")
    if not isinstance(jti, str) or not jti:
        raise ValueError("invalid mediamtx bearer jti")
    return {"act": act, "path": path, "exp": exp, "jti": jti}


def public_credential_response(issued: dict[str, Any]) -> dict[str, Any]:
    """Strip internal jti from API response (kept for registry only)."""
    out = {k: v for k, v in issued.items() if k != "jti"}
    return out
