"""Unit tests: CreateTournamentDraft + outbox marking (in-memory UoW)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.commands.create_tournament_draft import create_tournament_draft
from app.domain.tournament.events import TOURNAMENT_DRAFT_CREATED
from tests.fakes import InMemoryUnitOfWork


def test_create_tournament_draft_writes_aggregate_and_outbox() -> None:
    uow = InMemoryUnitOfWork()
    result = create_tournament_draft(uow, correlation_id="corr-test-1")

    assert uow.committed is True
    assert result["event_type"] == TOURNAMENT_DRAFT_CREATED
    assert result["tournament_id"] in uow.tournaments.items
    outbox = uow.outbox.items[result["outbox_id"]]
    assert outbox.correlation_id == "corr-test-1"
    assert outbox.aggregate_id == result["tournament_id"]
    assert outbox.processed_at is None


def test_outbox_mark_processed_idempotent() -> None:
    uow = InMemoryUnitOfWork()
    result = create_tournament_draft(uow, correlation_id="corr-2")
    message_id = result["outbox_id"]

    uow.outbox.mark_processed(message_id, when=datetime.now(UTC))
    first = uow.outbox.items[message_id].processed_at
    uow.outbox.mark_processed(message_id, when=datetime.now(UTC))
    assert uow.outbox.items[message_id].processed_at == first
    assert uow.outbox.list_unprocessed() == []
