"""Foundation probe — CreateTournamentDraft + outbox dispatch."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.application.commands.create_tournament_draft import create_tournament_draft
from app.infrastructure.outbox.dispatcher import dispatch_pending
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.middleware.correlation import get_correlation_id

router = APIRouter(prefix="/internal/foundation", tags=["foundation"])


@router.post("/probe")
def foundation_probe() -> dict[str, Any]:
    correlation_id = get_correlation_id()
    with SqlAlchemyUnitOfWork() as uow:
        result = create_tournament_draft(uow, correlation_id=correlation_id or None)
    dispatched = dispatch_pending()
    return {
        "tournament_id": result["tournament_id"],
        "outbox_id": result["outbox_id"],
        "event_type": result["event_type"],
        "correlation_id": correlation_id,
        "dispatched": dispatched,
    }
