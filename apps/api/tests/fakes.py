"""In-memory UoW for unit tests — no SQLAlchemy."""

from __future__ import annotations

from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

from app.domain.demo.entities import DemoFile
from app.domain.game_server.entities import GameServer
from app.domain.match.entities import Match
from app.domain.match.game_command import GameCommand
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.entities import Tournament


class InMemoryTournamentRepository:
    def __init__(self) -> None:
        self.items: dict[str, Tournament] = {}

    def add(self, tournament: Tournament) -> None:
        self.items[tournament.id] = tournament

    def get(self, tournament_id: str) -> Tournament | None:
        return self.items.get(tournament_id)


class InMemoryMatchRepository:
    def __init__(self) -> None:
        self.items: dict[str, Match] = {}

    def add(self, match: Match) -> None:
        self.items[match.id] = match

    def get(self, match_id: str) -> Match | None:
        return self.items.get(match_id)

    def save(self, match: Match) -> None:
        self.items[match.id] = match


class InMemoryGameEventRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}

    def exists(self, event_id: str) -> bool:
        return event_id in self.items

    def add(
        self,
        *,
        event_id: str,
        match_id: str,
        sequence: int,
        event_type: str,
        server_id: str,
        payload: dict[str, Any],
    ) -> None:
        self.items[event_id] = {
            "event_id": event_id,
            "match_id": match_id,
            "sequence": sequence,
            "event_type": event_type,
            "server_id": server_id,
            "payload": payload,
        }


class InMemoryGameCommandRepository:
    def __init__(self) -> None:
        self.items: dict[str, GameCommand] = {}

    def get(self, command_id: str) -> GameCommand | None:
        return self.items.get(command_id)

    def add(self, command: GameCommand) -> None:
        self.items[command.command_id] = command

    def save(self, command: GameCommand) -> None:
        self.items[command.command_id] = command


class InMemoryGameServerRepository:
    def __init__(self) -> None:
        self.items: dict[str, GameServer] = {}

    def add(self, server: GameServer) -> None:
        self.items[server.id] = server

    def get(self, server_id: str) -> GameServer | None:
        return self.items.get(server_id)

    def save(self, server: GameServer) -> None:
        self.items[server.id] = server

    def list(self, *, limit: int = 100) -> list[GameServer]:
        return list(self.items.values())[:limit]


class InMemoryDemoFileRepository:
    def __init__(self) -> None:
        self.items: dict[str, DemoFile] = {}

    def add(self, demo: DemoFile) -> None:
        self.items[demo.id] = demo

    def list_for_match(self, match_id: str) -> list[DemoFile]:
        return [d for d in self.items.values() if d.match_id == match_id]


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self.items: dict[str, OutboxMessage] = {}

    def add(self, message: OutboxMessage) -> None:
        self.items[message.id] = message

    def list_unprocessed(self, *, limit: int = 100) -> list[OutboxMessage]:
        pending = [m for m in self.items.values() if m.processed_at is None]
        pending.sort(key=lambda m: m.created_at or datetime.min.replace(tzinfo=UTC))
        return pending[:limit]

    def mark_processed(self, message_id: str, *, when: datetime | None = None) -> None:
        message = self.items[message_id]
        if message.processed_at is None:
            message.processed_at = when or datetime.now(UTC)


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.tournaments = InMemoryTournamentRepository()
        self.matches = InMemoryMatchRepository()
        self.game_events = InMemoryGameEventRepository()
        self.game_commands = InMemoryGameCommandRepository()
        self.game_servers = InMemoryGameServerRepository()
        self.demos = InMemoryDemoFileRepository()
        self.outbox = InMemoryOutboxRepository()
        self.committed = False

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

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False
