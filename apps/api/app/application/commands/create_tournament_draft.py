"""CreateTournamentDraft — aggregate + outbox in one UoW."""

from __future__ import annotations

from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.entities import Tournament
from app.domain.tournament.events import TOURNAMENT_DRAFT_CREATED


def create_tournament_draft(
    uow: UnitOfWork,
    *,
    correlation_id: str | None = None,
) -> dict[str, str]:
    """Persist draft tournament and outbox row; caller commits via UoW."""
    tournament_id = str(uuid4())
    outbox_id = str(uuid4())

    uow.tournaments.add(Tournament(id=tournament_id, status="draft"))
    uow.outbox.add(
        OutboxMessage(
            id=outbox_id,
            event_type=TOURNAMENT_DRAFT_CREATED,
            aggregate_type="tournament",
            aggregate_id=tournament_id,
            payload={"tournament_id": tournament_id, "status": "draft"},
            correlation_id=correlation_id,
        )
    )
    uow.commit()

    return {
        "tournament_id": tournament_id,
        "outbox_id": outbox_id,
        "event_type": TOURNAMENT_DRAFT_CREATED,
    }
