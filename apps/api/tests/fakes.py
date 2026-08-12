"""In-memory UoW for unit tests — no SQLAlchemy."""

from __future__ import annotations

from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

from app.domain.demo.entities import DemoFile
from app.domain.game_server.entities import GameServer
from app.domain.identity.entities import InviteToken
from app.domain.match.entities import Match
from app.domain.match.game_command import GameCommand
from app.domain.overlay.entities import OverlayState
from app.domain.production.entities import ProductionSession
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.bracket_entities import BracketNode
from app.domain.tournament.branding_entities import TournamentBranding
from app.domain.tournament.entities import Tournament
from app.domain.tournament.team_entities import Player, Team


class InMemoryTournamentRepository:
    def __init__(self) -> None:
        self.items: dict[str, Tournament] = {}

    def add(self, tournament: Tournament) -> None:
        self.items[tournament.id] = tournament

    def get(self, tournament_id: str) -> Tournament | None:
        return self.items.get(tournament_id)

    def save(self, tournament: Tournament) -> None:
        if tournament.id not in self.items:
            raise KeyError(f"tournament not found: {tournament.id}")
        self.items[tournament.id] = tournament

    def list(self, *, limit: int = 100) -> list[Tournament]:
        return list(self.items.values())[:limit]


class InMemoryTeamRepository:
    def __init__(self) -> None:
        self.items: dict[str, Team] = {}

    def add(self, team: Team) -> None:
        self.items[team.id] = team

    def get(self, team_id: str) -> Team | None:
        return self.items.get(team_id)

    def save(self, team: Team) -> None:
        if team.id not in self.items:
            raise KeyError(f"team not found: {team.id}")
        self.items[team.id] = team

    def delete(self, team_id: str) -> None:
        if team_id not in self.items:
            raise KeyError(f"team not found: {team_id}")
        del self.items[team_id]

    def list_for_tournament(self, tournament_id: str) -> list[Team]:
        return [t for t in self.items.values() if t.tournament_id == tournament_id]

    def find_by_name(self, tournament_id: str, name: str) -> Team | None:
        for t in self.items.values():
            if t.tournament_id == tournament_id and t.name == name:
                return t
        return None

    def count_for_tournament(self, tournament_id: str) -> int:
        return sum(1 for t in self.items.values() if t.tournament_id == tournament_id)


class InMemoryPlayerRepository:
    def __init__(self) -> None:
        self.items: dict[str, Player] = {}

    def add(self, player: Player) -> None:
        self.items[player.id] = player

    def get(self, player_id: str) -> Player | None:
        return self.items.get(player_id)

    def save(self, player: Player) -> None:
        if player.id not in self.items:
            raise KeyError(f"player not found: {player.id}")
        self.items[player.id] = player

    def delete(self, player_id: str) -> None:
        if player_id not in self.items:
            raise KeyError(f"player not found: {player_id}")
        del self.items[player_id]

    def list_for_team(self, team_id: str) -> list[Player]:
        return [p for p in self.items.values() if p.team_id == team_id]

    def delete_for_team(self, team_id: str) -> None:
        for pid in [p.id for p in self.items.values() if p.team_id == team_id]:
            del self.items[pid]

    def count_for_team(self, team_id: str) -> int:
        return sum(1 for p in self.items.values() if p.team_id == team_id)


class InMemoryBracketNodeRepository:
    def __init__(self) -> None:
        self.items: dict[str, BracketNode] = {}

    def add(self, node: BracketNode) -> None:
        self.items[node.id] = node

    def get(self, node_id: str) -> BracketNode | None:
        return self.items.get(node_id)

    def save(self, node: BracketNode) -> None:
        if node.id not in self.items:
            raise KeyError(f"bracket node not found: {node.id}")
        self.items[node.id] = node

    def list_for_tournament(self, tournament_id: str) -> list[BracketNode]:
        return [n for n in self.items.values() if n.tournament_id == tournament_id]

    def delete_for_tournament(self, tournament_id: str) -> None:
        for nid in [n.id for n in self.items.values() if n.tournament_id == tournament_id]:
            del self.items[nid]

    def count_for_tournament(self, tournament_id: str) -> int:
        return sum(1 for n in self.items.values() if n.tournament_id == tournament_id)


class InMemoryBrandingRepository:
    def __init__(self) -> None:
        self.items: dict[str, TournamentBranding] = {}

    def get(self, tournament_id: str) -> TournamentBranding | None:
        return self.items.get(tournament_id)

    def upsert(self, branding: TournamentBranding) -> None:
        self.items[branding.tournament_id] = branding


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


class InMemoryOverlayStateRepository:
    def __init__(self) -> None:
        self.items: dict[str, OverlayState] = {}

    def get(self, match_id: str) -> OverlayState | None:
        return self.items.get(match_id)

    def add(self, state: OverlayState) -> None:
        self.items[state.match_id] = state

    def save(self, state: OverlayState) -> None:
        self.items[state.match_id] = state


class InMemoryProductionSessionRepository:
    def __init__(self) -> None:
        self.items: dict[str, ProductionSession] = {}

    def get(self, match_id: str) -> ProductionSession | None:
        return self.items.get(match_id)

    def add(self, session: ProductionSession) -> None:
        self.items[session.match_id] = session

    def save(self, session: ProductionSession) -> None:
        self.items[session.match_id] = session


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


class InMemoryInviteTokenRepository:
    def __init__(self) -> None:
        self.items: dict[str, InviteToken] = {}
        self.by_hash: dict[str, str] = {}

    def add(self, invite: InviteToken) -> None:
        self.items[invite.id] = invite
        self.by_hash[invite.token_hash] = invite.id

    def get(self, invite_id: str) -> InviteToken | None:
        return self.items.get(invite_id)

    def get_by_hash(self, token_hash: str) -> InviteToken | None:
        invite_id = self.by_hash.get(token_hash)
        if invite_id is None:
            return None
        return self.items.get(invite_id)

    def save(self, invite: InviteToken) -> None:
        self.items[invite.id] = invite
        self.by_hash[invite.token_hash] = invite.id


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.tournaments = InMemoryTournamentRepository()
        self.teams = InMemoryTeamRepository()
        self.players = InMemoryPlayerRepository()
        self.bracket_nodes = InMemoryBracketNodeRepository()
        self.branding = InMemoryBrandingRepository()
        self.matches = InMemoryMatchRepository()
        self.game_events = InMemoryGameEventRepository()
        self.game_commands = InMemoryGameCommandRepository()
        self.game_servers = InMemoryGameServerRepository()
        self.demos = InMemoryDemoFileRepository()
        self.overlays = InMemoryOverlayStateRepository()
        self.production = InMemoryProductionSessionRepository()
        self.invites = InMemoryInviteTokenRepository()
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
