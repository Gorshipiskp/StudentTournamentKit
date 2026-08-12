"""Single-elim bracket node entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ALLOWED_BRACKET_SIZES = frozenset({4, 8})


@dataclass
class BracketNode:
    id: str
    tournament_id: str
    round: int
    position: int
    team_a_id: str | None = None
    team_b_id: str | None = None
    source_a_node_id: str | None = None
    source_b_node_id: str | None = None
    match_id: str | None = None

    def pair_ready(self) -> bool:
        return bool(self.team_a_id and self.team_b_id)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "round": self.round,
            "position": self.position,
            "team_a_id": self.team_a_id,
            "team_b_id": self.team_b_id,
            "source_a_node_id": self.source_a_node_id,
            "source_b_node_id": self.source_b_node_id,
            "match_id": self.match_id,
        }
