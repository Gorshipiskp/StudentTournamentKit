"""Invite create / redeem / revoke commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.identity.caps import ALLOWED_ROLES, caps_for_role
from app.domain.identity.entities import InviteSession, InviteToken
from app.infrastructure.security.session_token import (
    default_session_expiry,
    issue_session_token,
)
from app.infrastructure.security.token_hasher import generate_raw_token, hash_token

DEFAULT_INVITE_TTL = timedelta(days=7)


class InviteError(Exception):
    def __init__(self, message: str, *, code: str = "invite_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class CreatedInvite:
    invite: InviteToken
    raw_token: str

    def to_public_dict(self) -> dict[str, Any]:
        body = self.invite.to_public_dict(include_raw=self.raw_token)
        body["caps"] = sorted(caps_for_role(self.invite.role))
        return body


@dataclass(frozen=True)
class RedeemedSession:
    session: InviteSession
    access_token: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "token_type": "bearer",
            "invite_id": self.session.invite_id,
            "match_id": self.session.match_id,
            "role": self.session.role,
            "caps": sorted(self.session.caps),
            "expires_at": self.session.expires_at.isoformat(),
        }


def create_invite(
    uow: UnitOfWork,
    *,
    match_id: str,
    role: str,
    ttl_seconds: int | None = None,
    now: datetime | None = None,
) -> CreatedInvite:
    if role not in ALLOWED_ROLES:
        raise InviteError(f"unknown role: {role}", code="invalid_role")
    if uow.matches.get(match_id) is None:
        raise KeyError(f"match not found: {match_id}")

    clock = now or datetime.now(UTC)
    if ttl_seconds is not None:
        if ttl_seconds <= 0:
            raise InviteError("ttl_seconds must be positive", code="invalid_ttl")
        expires_at = clock + timedelta(seconds=ttl_seconds)
    else:
        expires_at = clock + DEFAULT_INVITE_TTL

    raw = generate_raw_token()
    invite = InviteToken(
        id=f"inv_{uuid4().hex[:12]}",
        token_hash=hash_token(raw),
        role=role,
        match_id=match_id,
        expires_at=expires_at,
        created_at=clock,
    )
    uow.invites.add(invite)
    uow.commit()
    return CreatedInvite(invite=invite, raw_token=raw)


def redeem_invite(
    uow: UnitOfWork,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> RedeemedSession:
    if not raw_token or not raw_token.strip():
        raise InviteError("token required", code="invalid_token")

    clock = now or datetime.now(UTC)
    invite = uow.invites.get_by_hash(hash_token(raw_token.strip()))
    if invite is None:
        raise InviteError("invite not found", code="not_found")
    if invite.is_revoked():
        raise InviteError("invite revoked", code="revoked")
    if invite.is_expired(now=clock):
        raise InviteError("invite expired", code="expired")

    session_exp = default_session_expiry(now=clock)
    if invite.expires_at.tzinfo is None:
        invite_exp = invite.expires_at.replace(tzinfo=UTC)
    else:
        invite_exp = invite.expires_at
    if session_exp > invite_exp:
        session_exp = invite_exp

    session = InviteSession(
        invite_id=invite.id,
        match_id=invite.match_id,
        role=invite.role,
        caps=caps_for_role(invite.role),
        expires_at=session_exp,
    )
    return RedeemedSession(session=session, access_token=issue_session_token(session))


def revoke_invite(
    uow: UnitOfWork,
    *,
    invite_id: str | None = None,
    raw_token: str | None = None,
    now: datetime | None = None,
) -> InviteToken:
    invite: InviteToken | None = None
    if invite_id:
        invite = uow.invites.get(invite_id)
    elif raw_token:
        invite = uow.invites.get_by_hash(hash_token(raw_token.strip()))
    else:
        raise InviteError("invite_id or token required", code="invalid_request")

    if invite is None:
        raise KeyError("invite not found")

    clock = now or datetime.now(UTC)
    invite.revoke(when=clock)
    uow.invites.save(invite)
    uow.commit()
    return invite
