"""SQLAlchemy repository adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.demo.entities import DemoFile
from app.domain.game_server.entities import GameServer
from app.domain.match.entities import Match
from app.domain.match.game_command import GameCommand
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.entities import Tournament
from app.infrastructure.persistence import models


def _match_from_row(row: models.Match) -> Match:
    return Match(
        id=row.id,
        tournament_id=row.tournament_id,
        status=row.status,
        review_status=row.review_status,
        review_resolution=row.review_resolution,
        version=row.version,
        score_team_a=row.score_team_a,
        score_team_b=row.score_team_b,
        round_number=row.round_number,
        map_name=row.map_name,
        phase=row.phase,
        game_server_id=row.game_server_id,
        last_sequence=row.last_sequence,
        reconcile_needed=bool(row.reconcile_needed),
        actual_paused=bool(row.actual_paused),
        desired_paused=bool(row.desired_paused),
        webhook_secret=row.webhook_secret,
        game_endpoint_url=row.game_endpoint_url,
    )


def _write_match_row(row: models.Match, match: Match) -> None:
    row.tournament_id = match.tournament_id
    row.status = match.status
    row.review_status = match.review_status
    row.review_resolution = match.review_resolution
    row.version = match.version
    row.score_team_a = match.score_team_a
    row.score_team_b = match.score_team_b
    row.round_number = match.round_number
    row.map_name = match.map_name
    row.phase = match.phase
    row.game_server_id = match.game_server_id
    row.last_sequence = match.last_sequence
    row.reconcile_needed = match.reconcile_needed
    row.actual_paused = match.actual_paused
    row.desired_paused = match.desired_paused
    row.webhook_secret = match.webhook_secret
    row.game_endpoint_url = match.game_endpoint_url


class SqlAlchemyTournamentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, tournament: Tournament) -> None:
        self._session.add(
            models.Tournament(
                id=tournament.id,
                status=tournament.status,
            )
        )

    def get(self, tournament_id: str) -> Tournament | None:
        row = self._session.get(models.Tournament, tournament_id)
        if row is None:
            return None
        return Tournament(id=row.id, status=row.status)


class SqlAlchemyMatchRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, match: Match) -> None:
        row = models.Match(
            id=match.id,
            tournament_id=match.tournament_id,
        )
        _write_match_row(row, match)
        self._session.add(row)

    def get(self, match_id: str) -> Match | None:
        row = self._session.get(models.Match, match_id)
        if row is None:
            return None
        return _match_from_row(row)

    def save(self, match: Match) -> None:
        row = self._session.get(models.Match, match.id)
        if row is None:
            raise KeyError(f"match not found: {match.id}")
        _write_match_row(row, match)


class SqlAlchemyGameEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def exists(self, event_id: str) -> bool:
        return self._session.get(models.GameEvent, event_id) is not None

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
        self._session.add(
            models.GameEvent(
                event_id=event_id,
                match_id=match_id,
                sequence=sequence,
                event_type=event_type,
                server_id=server_id,
                payload=payload,
            )
        )


class SqlAlchemyGameCommandRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, command_id: str) -> GameCommand | None:
        row = self._session.get(models.GameCommand, command_id)
        if row is None:
            return None
        return GameCommand(
            command_id=row.command_id,
            match_id=row.match_id,
            command_type=row.command_type,
            status=row.status,
            payload=dict(row.payload) if row.payload else None,
            ack_status=row.ack_status,
            ack_error=row.ack_error,
            ack_result=dict(row.ack_result) if row.ack_result else None,
            correlation_id=row.correlation_id,
            created_at=row.created_at,
            sent_at=row.sent_at,
            ack_at=row.ack_at,
        )

    def add(self, command: GameCommand) -> None:
        self._session.add(
            models.GameCommand(
                command_id=command.command_id,
                match_id=command.match_id,
                command_type=command.command_type,
                status=command.status,
                payload=command.payload,
                ack_status=command.ack_status,
                ack_error=command.ack_error,
                ack_result=command.ack_result,
                correlation_id=command.correlation_id,
                sent_at=command.sent_at,
                ack_at=command.ack_at,
            )
        )

    def save(self, command: GameCommand) -> None:
        row = self._session.get(models.GameCommand, command.command_id)
        if row is None:
            raise KeyError(f"command not found: {command.command_id}")
        row.status = command.status
        row.payload = command.payload
        row.ack_status = command.ack_status
        row.ack_error = command.ack_error
        row.ack_result = command.ack_result
        row.correlation_id = command.correlation_id
        row.sent_at = command.sent_at
        row.ack_at = command.ack_at


class SqlAlchemyGameServerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, server: GameServer) -> None:
        self._session.add(
            models.GameServer(
                id=server.id,
                status=server.status,
                host=server.host,
                port=server.port,
                endpoint_url=server.endpoint_url,
                webhook_secret=server.webhook_secret,
                assigned_match_id=server.assigned_match_id,
                last_heartbeat=server.last_heartbeat,
                bridge_version=server.bridge_version,
                protocol_version=server.protocol_version,
            )
        )

    def get(self, server_id: str) -> GameServer | None:
        row = self._session.get(models.GameServer, server_id)
        if row is None:
            return None
        return _server_from_row(row)

    def save(self, server: GameServer) -> None:
        row = self._session.get(models.GameServer, server.id)
        if row is None:
            raise KeyError(f"server not found: {server.id}")
        row.status = server.status
        row.host = server.host
        row.port = server.port
        row.endpoint_url = server.endpoint_url
        row.webhook_secret = server.webhook_secret
        row.assigned_match_id = server.assigned_match_id
        row.last_heartbeat = server.last_heartbeat
        row.bridge_version = server.bridge_version
        row.protocol_version = server.protocol_version

    def list(self, *, limit: int = 100) -> list[GameServer]:
        rows = self._session.scalars(
            select(models.GameServer).order_by(models.GameServer.id.asc()).limit(limit)
        ).all()
        return [_server_from_row(r) for r in rows]


def _server_from_row(row: models.GameServer) -> GameServer:
    return GameServer(
        id=row.id,
        status=row.status,
        host=row.host,
        port=row.port,
        endpoint_url=row.endpoint_url,
        webhook_secret=row.webhook_secret,
        assigned_match_id=row.assigned_match_id,
        last_heartbeat=row.last_heartbeat,
        bridge_version=row.bridge_version,
        protocol_version=row.protocol_version,
    )


class SqlAlchemyDemoFileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, demo: DemoFile) -> None:
        self._session.add(
            models.DemoFile(
                id=demo.id,
                match_id=demo.match_id,
                durable_uri=demo.durable_uri,
                size_bytes=demo.size_bytes,
                map_name=demo.map_name,
                source_uri=demo.source_uri,
            )
        )

    def list_for_match(self, match_id: str) -> list[DemoFile]:
        rows = self._session.scalars(
            select(models.DemoFile)
            .where(models.DemoFile.match_id == match_id)
            .order_by(models.DemoFile.created_at.asc())
        ).all()
        return [
            DemoFile(
                id=r.id,
                match_id=r.match_id,
                durable_uri=r.durable_uri,
                size_bytes=r.size_bytes,
                map_name=r.map_name,
                source_uri=r.source_uri,
                created_at=r.created_at,
            )
            for r in rows
        ]


class SqlAlchemyOutboxRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, message: OutboxMessage) -> None:
        self._session.add(
            models.EventOutbox(
                id=message.id,
                event_type=message.event_type,
                aggregate_type=message.aggregate_type,
                aggregate_id=message.aggregate_id,
                payload=message.payload,
                correlation_id=message.correlation_id,
            )
        )

    def list_unprocessed(self, *, limit: int = 100) -> list[OutboxMessage]:
        rows = self._session.scalars(
            select(models.EventOutbox)
            .where(models.EventOutbox.processed_at.is_(None))
            .order_by(models.EventOutbox.created_at.asc())
            .limit(limit)
        ).all()
        return [
            OutboxMessage(
                id=row.id,
                event_type=row.event_type,
                aggregate_type=row.aggregate_type,
                aggregate_id=row.aggregate_id,
                payload=dict(row.payload or {}),
                correlation_id=row.correlation_id,
                created_at=row.created_at,
                processed_at=row.processed_at,
            )
            for row in rows
        ]

    def mark_processed(self, message_id: str, *, when: datetime | None = None) -> None:
        row = self._session.get(models.EventOutbox, message_id)
        if row is None or row.processed_at is not None:
            return
        row.processed_at = when or datetime.now(UTC)
