"""Match aggregate — lifecycle + game view (no MatchZy/RCON)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


from app.domain.match.review import (
    REVIEW_NONE,
    REVIEW_PAUSE_PENDING,
    REVIEW_PAUSED,
    REVIEW_REQUESTED,
)


MATCH_SCHEDULED = "scheduled"
MATCH_SERVER_ASSIGNED = "server_assigned"
MATCH_WARMUP = "warmup"
MATCH_KNIFE = "knife"
MATCH_LIVE = "live"
MATCH_MAP_END = "map_end"
MATCH_COMPLETED = "completed"
MATCH_CANCELLED = "cancelled"
MATCH_FORFEITED = "forfeited"


@dataclass
class Match:
    id: str
    tournament_id: str
    status: str = MATCH_SCHEDULED
    review_status: str = REVIEW_NONE
    review_resolution: str | None = None
    version: int = 1
    score_team_a: int = 0
    score_team_b: int = 0
    round_number: int = 0
    map_name: str | None = None
    phase: str = "warmup"
    game_server_id: str | None = None
    last_sequence: int = 0
    reconcile_needed: bool = False
    actual_paused: bool = False
    desired_paused: bool = False
    webhook_secret: str | None = None
    game_endpoint_url: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        split_brain = self.desired_paused != self.actual_paused
        banner = None
        if self.review_status == REVIEW_REQUESTED:
            banner = "review_requested"
        elif self.review_status == REVIEW_PAUSE_PENDING:
            banner = "pause_pending"
        elif self.review_status == REVIEW_PAUSED:
            banner = "tech_pause"
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "status": self.status,
            "review_status": self.review_status,
            "review_resolution": self.review_resolution,
            "version": self.version,
            "score": {"team_a": self.score_team_a, "team_b": self.score_team_b},
            "round": self.round_number,
            "map": self.map_name,
            "phase": self.phase,
            "game_server_id": self.game_server_id,
            "game_endpoint_url": self.game_endpoint_url,
            "last_sequence": self.last_sequence,
            "reconcile_needed": self.reconcile_needed,
            "actual_paused": self.actual_paused,
            "desired_paused": self.desired_paused,
            "split_brain": split_brain,
            "judge_banner": banner,
        }


@dataclass(frozen=True)
class ApplyResult:
    applied: bool
    reason: str
    status_changed: bool = False
    score_changed: bool = False
    previous_status: str | None = None
    transitions: tuple[str, ...] = field(default_factory=tuple)
