"""Invite token aggregate (opaque secret never stored)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class InviteToken:
    id: str
    token_hash: str
    role: str
    match_id: str
    expires_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime | None = None

    def is_revoked(self, *, now: datetime | None = None) -> bool:
        return self.revoked_at is not None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        clock = now or datetime.now(UTC)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return clock >= exp

    def is_usable(self, *, now: datetime | None = None) -> bool:
        return not self.is_revoked() and not self.is_expired(now=now)

    def revoke(self, *, when: datetime | None = None) -> None:
        if self.revoked_at is None:
            self.revoked_at = when or datetime.now(UTC)

    def to_public_dict(self, *, include_raw: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "invite_id": self.id,
            "role": self.role,
            "match_id": self.match_id,
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked_at is not None,
        }
        if include_raw is not None:
            body["token"] = include_raw
        return body


@dataclass(frozen=True)
class InviteSession:
    """Short-lived session claims after redeem (not a DB row)."""

    invite_id: str
    match_id: str
    role: str
    caps: frozenset[str]
    expires_at: datetime

    def has_cap(self, cap: str) -> bool:
        return cap in self.caps

    def requires_match(self, match_id: str) -> bool:
        return self.match_id == match_id
