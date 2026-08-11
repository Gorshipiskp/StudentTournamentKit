"""Game command aggregate (Platform → CS2 / Fake)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

CMD_REQUESTED = "requested"
CMD_SENT = "sent"
CMD_CONFIRMED = "confirmed"
CMD_FAILED = "failed"

TYPE_PAUSE = "PauseMatch"
TYPE_RESUME = "ResumeMatch"
TYPE_FORFEIT = "ForfeitMatch"
TYPE_LOAD = "LoadMatch"
TYPE_SNAPSHOT = "GetSnapshot"


@dataclass
class GameCommand:
    command_id: str
    match_id: str
    command_type: str
    status: str = CMD_REQUESTED
    payload: dict[str, Any] | None = None
    ack_status: str | None = None
    ack_error: str | None = None
    ack_result: dict[str, Any] | None = None
    correlation_id: str | None = None
    created_at: datetime | None = None
    sent_at: datetime | None = None
    ack_at: datetime | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "match_id": self.match_id,
            "type": self.command_type,
            "status": self.status,
            "payload": self.payload or {},
            "ack_status": self.ack_status,
            "ack_error": self.ack_error,
            "ack_result": self.ack_result,
            "correlation_id": self.correlation_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "ack_at": self.ack_at.isoformat() if self.ack_at else None,
            # HTTP 200 on wire ≠ success — explicit flags for clients
            "delivery_ok": self.status in {CMD_SENT, CMD_CONFIRMED, CMD_FAILED}
            and self.ack_status is not None,
            "confirmed": self.status == CMD_CONFIRMED,
        }
