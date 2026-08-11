"""After-commit outbox dispatcher (in-process, single replica)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger("stp.outbox")


def handle_outbox_message(message: OutboxMessage) -> None:
    """Side-effect handler — Foundation: structured no-op log."""
    logger.info(
        "outbox_handled event_type=%s aggregate=%s/%s correlation_id=%s",
        message.event_type,
        message.aggregate_type,
        message.aggregate_id,
        message.correlation_id,
    )


def dispatch_pending(*, limit: int = 100) -> int:
    """Process unprocessed outbox rows; idempotent on already-processed."""
    processed = 0
    with SqlAlchemyUnitOfWork() as uow:
        pending = uow.outbox.list_unprocessed(limit=limit)
        now = datetime.now(UTC)
        for message in pending:
            handle_outbox_message(message)
            uow.outbox.mark_processed(message.id, when=now)
            processed += 1
        if processed:
            uow.commit()
    return processed
