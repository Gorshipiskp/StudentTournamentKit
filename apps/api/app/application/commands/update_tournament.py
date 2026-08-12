"""Update / publish tournament commands."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.create_tournament_draft import TournamentError
from app.application.unit_of_work import UnitOfWork
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.entities import (
    ALLOWED_FORMATS,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    Tournament,
)
from app.domain.tournament.events import TOURNAMENT_PUBLISHED, TOURNAMENT_UPDATED


def update_tournament(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    name: str | None = None,
    format: str | None = None,
    settings: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> Tournament:
    tournament = uow.tournaments.get(tournament_id)
    if tournament is None:
        raise KeyError(f"tournament not found: {tournament_id}")

    if name is not None:
        tournament.name = name.strip()
    if format is not None:
        fmt = format.strip()
        if fmt not in ALLOWED_FORMATS:
            raise TournamentError(f"unsupported format: {fmt}", code="bad_format")
        if tournament.status != STATUS_DRAFT and fmt != tournament.format:
            raise TournamentError(
                "format can only change while draft",
                code="frozen_format",
            )
        tournament.format = fmt
    if settings is not None:
        tournament.settings_json = dict(settings)

    uow.tournaments.save(tournament)
    uow.outbox.add(
        OutboxMessage(
            id=str(uuid4()),
            event_type=TOURNAMENT_UPDATED,
            aggregate_type="tournament",
            aggregate_id=tournament.id,
            payload={"tournament_id": tournament.id, "status": tournament.status},
            correlation_id=correlation_id,
        )
    )
    uow.commit()
    return tournament


def publish_tournament(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    correlation_id: str | None = None,
) -> Tournament:
    tournament = uow.tournaments.get(tournament_id)
    if tournament is None:
        raise KeyError(f"tournament not found: {tournament_id}")
    if tournament.status != STATUS_DRAFT:
        raise TournamentError(
            f"cannot publish from status={tournament.status}",
            code="bad_status",
        )
    if not tournament.name.strip():
        raise TournamentError("name required before publish", code="name_required")

    tournament.status = STATUS_PUBLISHED
    uow.tournaments.save(tournament)
    uow.outbox.add(
        OutboxMessage(
            id=str(uuid4()),
            event_type=TOURNAMENT_PUBLISHED,
            aggregate_type="tournament",
            aggregate_id=tournament.id,
            payload={"tournament_id": tournament.id, "status": STATUS_PUBLISHED},
            correlation_id=correlation_id,
        )
    )
    uow.commit()
    return tournament
