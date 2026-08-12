"""CreateTournamentDraft — aggregate + outbox in one UoW."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.entities import (
    ALLOWED_FORMATS,
    FORMAT_SINGLE_ELIM,
    STATUS_DRAFT,
    Tournament,
)
from app.domain.tournament.events import TOURNAMENT_DRAFT_CREATED


class TournamentError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def create_tournament_draft(
    uow: UnitOfWork,
    *,
    name: str = "",
    format: str = FORMAT_SINGLE_ELIM,
    settings: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Persist draft tournament and outbox row; caller commits via UoW."""
    fmt = (format or FORMAT_SINGLE_ELIM).strip()
    if fmt not in ALLOWED_FORMATS:
        raise TournamentError(f"unsupported format: {fmt}", code="bad_format")

    tournament_id = str(uuid4())
    outbox_id = str(uuid4())
    settings_json = dict(settings or {})

    tournament = Tournament(
        id=tournament_id,
        status=STATUS_DRAFT,
        name=(name or "").strip(),
        format=fmt,
        settings_json=settings_json,
    )
    uow.tournaments.add(tournament)
    uow.outbox.add(
        OutboxMessage(
            id=outbox_id,
            event_type=TOURNAMENT_DRAFT_CREATED,
            aggregate_type="tournament",
            aggregate_id=tournament_id,
            payload={
                "tournament_id": tournament_id,
                "status": STATUS_DRAFT,
                "name": tournament.name,
                "format": tournament.format,
            },
            correlation_id=correlation_id,
        )
    )
    uow.commit()

    return {
        "tournament_id": tournament_id,
        "outbox_id": outbox_id,
        "event_type": TOURNAMENT_DRAFT_CREATED,
        "tournament": tournament.to_public_dict(),
    }
