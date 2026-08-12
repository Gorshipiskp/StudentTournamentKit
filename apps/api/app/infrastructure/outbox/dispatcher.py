"""After-commit outbox dispatcher (in-process, single replica)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.domain.match.messages import (
    JUDGE_NOTIFY_EVENTS,
    PROTOCOL_VERSION,
    TYPE_MATCH_STATUS,
)
from app.domain.overlay.entities import OVERLAY_UPDATED
from app.domain.production.entities import PRODUCTION_DESIRED_CHANGED
from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger("stk.outbox")


def handle_outbox_message(message: OutboxMessage) -> None:
    """Side-effect handler — overlay/agent/judge WS fanout + structured log."""
    logger.info(
        "outbox_handled event_type=%s aggregate=%s/%s correlation_id=%s",
        message.event_type,
        message.aggregate_type,
        message.aggregate_id,
        message.correlation_id,
    )
    if message.event_type == OVERLAY_UPDATED:
        # Late import so tests can swap hub singleton.
        from app.infrastructure.realtime.overlay_hub import overlay_hub as hub

        payload = message.payload.get("message")
        if isinstance(payload, dict):
            hub.publish(message.aggregate_id, payload)
        else:
            logger.warning(
                "overlay.updated missing message payload aggregate_id=%s",
                message.aggregate_id,
            )
    elif message.event_type == PRODUCTION_DESIRED_CHANGED:
        from app.infrastructure.realtime.agent_hub import agent_hub as hub

        payload = message.payload.get("message")
        if isinstance(payload, dict):
            hub.publish(message.aggregate_id, payload)
        else:
            logger.warning(
                "production.desired_changed missing message payload aggregate_id=%s",
                message.aggregate_id,
            )
    elif message.event_type in JUDGE_NOTIFY_EVENTS:
        from app.infrastructure.realtime.judge_hub import judge_hub as hub

        match_body = message.payload.get("match")
        if not isinstance(match_body, dict):
            match_body = {
                "id": message.aggregate_id,
                "review_status": message.payload.get("review_status"),
                "review_resolution": message.payload.get("review_resolution"),
                "status": message.payload.get("match_status"),
                "version": message.payload.get("version"),
            }
        hub.publish(
            message.aggregate_id,
            {
                "protocol": PROTOCOL_VERSION,
                "type": TYPE_MATCH_STATUS,
                "match_id": message.aggregate_id,
                "reason": message.event_type,
                "match": match_body,
            },
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
