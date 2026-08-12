"""Unit: organizer token + tournament create/publish."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.application.commands.create_tournament_draft import (
    TournamentError,
    create_tournament_draft,
)
from app.application.commands.update_tournament import publish_tournament, update_tournament
from app.domain.tournament.entities import STATUS_DRAFT, STATUS_PUBLISHED
from app.infrastructure.security.organizer_token import (
    issue_organizer_token,
    parse_organizer_token,
    verify_organizer_credentials,
)
from tests.fakes import InMemoryUnitOfWork


def test_organizer_credentials_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STK_ORGANIZER_USERNAME", "org")
    monkeypatch.setenv("STK_ORGANIZER_PASSWORD", "secret")
    monkeypatch.setenv("STK_SESSION_SECRET", "unit_secret")

    assert verify_organizer_credentials("org", "secret")
    assert not verify_organizer_credentials("org", "wrong")
    assert not verify_organizer_credentials("other", "secret")

    token, session = issue_organizer_token(secret="unit_secret")
    parsed = parse_organizer_token(token, secret="unit_secret")
    assert parsed.role == "organizer"
    assert int(parsed.expires_at.timestamp()) == int(session.expires_at.timestamp())

    with pytest.raises(ValueError, match="expired"):
        parse_organizer_token(
            token,
            secret="unit_secret",
            now=datetime.now(UTC) + timedelta(hours=24),
        )


def test_create_and_publish_tournament() -> None:
    uow = InMemoryUnitOfWork()
    created = create_tournament_draft(
        uow,
        name="Кубок",
        format="single_elim",
        settings={"configured_broadcast_delay_seconds": 45},
    )
    tid = created["tournament_id"]
    t = uow.tournaments.get(tid)
    assert t is not None
    assert t.status == STATUS_DRAFT
    assert t.name == "Кубок"
    assert t.settings_json["configured_broadcast_delay_seconds"] == 45

    published = publish_tournament(uow, tournament_id=tid)
    assert published.status == STATUS_PUBLISHED

    with pytest.raises(TournamentError, match="cannot publish"):
        publish_tournament(uow, tournament_id=tid)


def test_publish_requires_name() -> None:
    uow = InMemoryUnitOfWork()
    created = create_tournament_draft(uow, name="")
    with pytest.raises(TournamentError, match="name required"):
        publish_tournament(uow, tournament_id=created["tournament_id"])


def test_update_tournament_fields() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="A")["tournament_id"]
    updated = update_tournament(
        uow,
        tournament_id=tid,
        name="B",
        settings={"configured_broadcast_delay_seconds": 10},
    )
    assert updated.name == "B"
    assert updated.settings_json["configured_broadcast_delay_seconds"] == 10


def test_create_match_still_auto_creates_tournament() -> None:
    from app.application.commands.create_match import create_match

    uow = InMemoryUnitOfWork()
    match = create_match(uow, match_id="m_auto", game_server_id="srv")
    t = uow.tournaments.get(match.tournament_id)
    assert t is not None
    assert t.status == STATUS_DRAFT
    assert t.format == "single_elim"
