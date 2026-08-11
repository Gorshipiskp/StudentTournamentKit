"""Outbox message — durable side-effect intent (domain view)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class OutboxMessage:
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None


class OutboxRepository(Protocol):
    def add(self, message: OutboxMessage) -> None: ...

    def list_unprocessed(self, *, limit: int = 100) -> list[OutboxMessage]: ...

    def mark_processed(self, message_id: str, *, when: datetime | None = None) -> None: ...
