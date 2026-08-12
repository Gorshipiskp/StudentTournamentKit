"""Application Unit of Work port."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from app.domain.demo.ports import DemoFileRepository
from app.domain.game_server.ports import GameServerRepository
from app.domain.identity.ports import InviteTokenRepository
from app.domain.match.ports import (
    GameCommandRepository,
    GameEventRepository,
    MatchRepository,
)
from app.domain.overlay.ports import OverlayStateRepository
from app.domain.production.ports import ProductionSessionRepository
from app.domain.shared.outbox import OutboxRepository
from app.domain.tournament.bracket_ports import BracketNodeRepository
from app.domain.tournament.branding_ports import BrandingRepository
from app.domain.tournament.ports import TournamentRepository
from app.domain.tournament.team_ports import PlayerRepository, TeamRepository


class UnitOfWork(Protocol):
    tournaments: TournamentRepository
    teams: TeamRepository
    players: PlayerRepository
    bracket_nodes: BracketNodeRepository
    branding: BrandingRepository
    matches: MatchRepository
    game_events: GameEventRepository
    game_commands: GameCommandRepository
    game_servers: GameServerRepository
    demos: DemoFileRepository
    overlays: OverlayStateRepository
    production: ProductionSessionRepository
    invites: InviteTokenRepository
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
