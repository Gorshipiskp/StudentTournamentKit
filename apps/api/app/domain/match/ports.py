"""Ports for match + game event dedup + game commands persistence."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.match.entities import Match
from app.domain.match.game_command import GameCommand


class MatchRepository(Protocol):
    def add(self, match: Match) -> None: ...

    def get(self, match_id: str) -> Match | None: ...

    def save(self, match: Match) -> None: ...


class GameEventRepository(Protocol):
    def exists(self, event_id: str) -> bool: ...

    def add(
        self,
        *,
        event_id: str,
        match_id: str,
        sequence: int,
        event_type: str,
        server_id: str,
        payload: dict[str, Any],
    ) -> None: ...


class GameCommandRepository(Protocol):
    def get(self, command_id: str) -> GameCommand | None: ...

    def add(self, command: GameCommand) -> None: ...

    def save(self, command: GameCommand) -> None: ...
