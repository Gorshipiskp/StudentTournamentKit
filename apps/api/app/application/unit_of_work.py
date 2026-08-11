"""Application Unit of Work port."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from app.domain.demo.ports import DemoFileRepository
from app.domain.game_server.ports import GameServerRepository
from app.domain.match.ports import (
    GameCommandRepository,
    GameEventRepository,
    MatchRepository,
)
from app.domain.shared.outbox import OutboxRepository
from app.domain.tournament.ports import TournamentRepository


class UnitOfWork(Protocol):
    tournaments: TournamentRepository
    matches: MatchRepository
    game_events: GameEventRepository
    game_commands: GameCommandRepository
    game_servers: GameServerRepository
    demos: DemoFileRepository
    outbox: OutboxRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
