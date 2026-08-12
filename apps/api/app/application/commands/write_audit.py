"""Write match audit entries (A10)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.audit.entities import MatchAuditEntry


def write_audit(
    uow: UnitOfWork,
    *,
    match_id: str,
    action: str,
    actor_type: str,
    actor_id: str | None = None,
    tournament_id: str | None = None,
    payload: dict[str, Any] | None = None,
    result: str = "ok",
    correlation_id: str | None = None,
    request_id: str | None = None,
) -> MatchAuditEntry:
    """
    Persist one audit row. Does not commit — caller owns the transaction.

    If tournament_id omitted, resolved from match when present.
    """
    tid = tournament_id
    if tid is None:
        match = uow.matches.get(match_id)
        if match is not None:
            tid = match.tournament_id

    entry = MatchAuditEntry(
        id=str(uuid4()),
        match_id=match_id,
        tournament_id=tid,
        correlation_id=correlation_id,
        request_id=request_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        payload=dict(payload or {}),
        result=result,
    )
    uow.audit.add(entry)
    return entry
