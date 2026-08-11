"""SQLAlchemy Unit of Work."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from app.infrastructure.persistence.repositories import (
    SqlAlchemyDemoFileRepository,
    SqlAlchemyGameCommandRepository,
    SqlAlchemyGameEventRepository,
    SqlAlchemyGameServerRepository,
    SqlAlchemyMatchRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyTournamentRepository,
)
from app.infrastructure.persistence.session import get_session_factory


class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session | None = None) -> None:
        self._owned_session = session is None
        self.session = session or get_session_factory()()
        self.tournaments = SqlAlchemyTournamentRepository(self.session)
        self.matches = SqlAlchemyMatchRepository(self.session)
        self.game_events = SqlAlchemyGameEventRepository(self.session)
        self.game_commands = SqlAlchemyGameCommandRepository(self.session)
        self.game_servers = SqlAlchemyGameServerRepository(self.session)
        self.demos = SqlAlchemyDemoFileRepository(self.session)
        self.outbox = SqlAlchemyOutboxRepository(self.session)

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
