"""Unit: invite create/redeem/revoke + caps + session match scope."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.commands.create_match import create_match
from app.application.commands.invite_tokens import (
    InviteError,
    create_invite,
    redeem_invite,
    revoke_invite,
)
from app.domain.identity.caps import (
    CAP_COMMENTATOR_WATCH,
    CAP_JUDGE_RESOLVE,
    CAP_JUDGE_REVIEW,
    CAP_OVERLAY_READ,
)
from app.infrastructure.security.session_token import parse_session_token
from tests.fakes import InMemoryUnitOfWork


def _match(uow: InMemoryUnitOfWork, match_id: str = "m_inv") -> str:
    create_match(uow, match_id=match_id, game_server_id="srv", webhook_secret="s")
    return match_id


def test_create_redeem_judge_caps() -> None:
    uow = InMemoryUnitOfWork()
    match_id = _match(uow)
    created = create_invite(uow, match_id=match_id, role="judge")
    assert created.raw_token
    assert len(created.raw_token) >= 32
    assert created.invite.token_hash != created.raw_token

    redeemed = redeem_invite(uow, raw_token=created.raw_token)
    assert redeemed.session.match_id == match_id
    assert redeemed.session.role == "judge"
    assert CAP_JUDGE_REVIEW in redeemed.session.caps
    assert CAP_JUDGE_RESOLVE in redeemed.session.caps
    assert CAP_COMMENTATOR_WATCH not in redeemed.session.caps

    session = parse_session_token(redeemed.access_token)
    assert session.invite_id == created.invite.id
    assert session.has_cap(CAP_JUDGE_REVIEW)


def test_redeem_commentator_caps() -> None:
    uow = InMemoryUnitOfWork()
    match_id = _match(uow, "m_com")
    created = create_invite(uow, match_id=match_id, role="commentator")
    redeemed = redeem_invite(uow, raw_token=created.raw_token)
    assert CAP_COMMENTATOR_WATCH in redeemed.session.caps
    assert CAP_OVERLAY_READ in redeemed.session.caps
    assert CAP_JUDGE_REVIEW not in redeemed.session.caps


def test_revoke_blocks_redeem() -> None:
    uow = InMemoryUnitOfWork()
    match_id = _match(uow)
    created = create_invite(uow, match_id=match_id, role="judge")
    revoke_invite(uow, invite_id=created.invite.id)
    with pytest.raises(InviteError) as exc:
        redeem_invite(uow, raw_token=created.raw_token)
    assert exc.value.code == "revoked"


def test_expired_invite_rejects_redeem() -> None:
    uow = InMemoryUnitOfWork()
    match_id = _match(uow)
    past = datetime.now(UTC) - timedelta(hours=1)
    created = create_invite(
        uow,
        match_id=match_id,
        role="judge",
        ttl_seconds=60,
        now=past - timedelta(minutes=5),
    )
    with pytest.raises(InviteError) as exc:
        redeem_invite(uow, raw_token=created.raw_token, now=datetime.now(UTC))
    assert exc.value.code == "expired"


def test_wrong_match_scope_on_session() -> None:
    uow = InMemoryUnitOfWork()
    match_a = _match(uow, "m_a")
    _match(uow, "m_b")
    created = create_invite(uow, match_id=match_a, role="judge")
    redeemed = redeem_invite(uow, raw_token=created.raw_token)
    session = parse_session_token(redeemed.access_token)
    assert session.requires_match("m_a")
    assert not session.requires_match("m_b")


def test_create_unknown_role() -> None:
    uow = InMemoryUnitOfWork()
    match_id = _match(uow)
    with pytest.raises(InviteError) as exc:
        create_invite(uow, match_id=match_id, role="admin")
    assert exc.value.code == "invalid_role"
