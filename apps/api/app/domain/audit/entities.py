"""Match audit log — durable operator/system trail (A10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Canonical action names (ARCHITECTURE §17.2)
ACTION_JUDGE_REVIEW_REQUEST = "judge.review_request"
ACTION_JUDGE_REVIEW_RESOLVE = "judge.review_resolve"
ACTION_JUDGE_FORFEIT = "judge.forfeit"
ACTION_DIRECTOR_SCENE_CHANGE = "director.scene_change"
ACTION_DIRECTOR_SCORE_OVERRIDE = "director.score_override"
ACTION_ORGANIZER_MATCH_START = "organizer.match_start"
ACTION_ORGANIZER_SCORE_SYNC = "organizer.score_sync"
ACTION_SYSTEM_ROUND_END = "system.round_end"

ACTOR_ORGANIZER = "organizer"
ACTOR_JUDGE = "judge"
ACTOR_DIRECTOR = "director"
ACTOR_SYSTEM = "system"


@dataclass
class MatchAuditEntry:
    id: str
    match_id: str
    action: str
    actor_type: str
    tournament_id: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    result: str = "ok"
    created_at: datetime | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "tournament_id": self.tournament_id,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "action": self.action,
            "payload": dict(self.payload),
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
