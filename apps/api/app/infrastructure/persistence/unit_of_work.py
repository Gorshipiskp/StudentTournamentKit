"""SQLAlchemy Unit of Work."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from app.infrastructure.persistence.repositories import (
    SqlAlchemyBracketNodeRepository,
    SqlAlchemyBrandingRepository,
    SqlAlchemyDemoFileRepository,
    SqlAlchemyGameCommandRepository,
    SqlAlchemyGameEventRepository,
    SqlAlchemyGameServerRepository,
    SqlAlchemyInviteTokenRepository,
    SqlAlchemyMatchAuditLogRepository,
    SqlAlchemyMatchRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyOverlayStateRepository,
    SqlAlchemyPlayerRepository,
    SqlAlchemyProductionSessionRepository,
    SqlAlchemyTeamRepository,
    SqlAlchemyTournamentRepository,
)
from app.infrastructure.persistence.session import get_session_factory


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session | None = None) -> None:
        self._owned_session = session is None
        self.session = session or get_session_factory()()
        self.tournaments = SqlAlchemyTournamentRepository(self.session)
        self.teams = SqlAlchemyTeamRepository(self.session)
        self.players = SqlAlchemyPlayerRepository(self.session)
        self.bracket_nodes = SqlAlchemyBracketNodeRepository(self.session)
        self.branding = SqlAlchemyBrandingRepository(self.session)
        self.matches = SqlAlchemyMatchRepository(self.session)
        self.game_events = SqlAlchemyGameEventRepository(self.session)
        self.game_commands = SqlAlchemyGameCommandRepository(self.session)
        self.game_servers = SqlAlchemyGameServerRepository(self.session)
        self.demos = SqlAlchemyDemoFileRepository(self.session)
        self.overlays = SqlAlchemyOverlayStateRepository(self.session)
        self.production = SqlAlchemyProductionSessionRepository(self.session)
        self.invites = SqlAlchemyInviteTokenRepository(self.session)
        self.outbox = SqlAlchemyOutboxRepository(self.session)
        self.audit = SqlAlchemyMatchAuditLogRepository(self.session)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        if self._owned_session:
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def flush(self) -> None:
        self.session.flush()

    def rollback(self) -> None:
        self.session.rollback()
