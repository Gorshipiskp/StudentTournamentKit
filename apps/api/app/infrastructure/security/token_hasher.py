"""Hash opaque invite tokens (store hash only — F4)."""

from __future__ import annotations

import hashlib
import secrets


TOKEN_BYTES = 32


def generate_raw_token(*, nbytes: int = TOKEN_BYTES) -> str:
    if nbytes < TOKEN_BYTES:
        raise ValueError(f"invite token must be >= {TOKEN_BYTES} bytes")
    return secrets.token_urlsafe(nbytes)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
