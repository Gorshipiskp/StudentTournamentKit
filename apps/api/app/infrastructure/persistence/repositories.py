"""SQLAlchemy repository adapters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.demo.entities import DemoFile
from app.domain.game_server.entities import GameServer
from app.domain.identity.entities import InviteToken
from app.domain.audit.entities import MatchAuditEntry
from app.domain.match.entities import Match
from app.domain.match.game_command import GameCommand
from app.domain.overlay.entities import OverlayState
from app.domain.production.entities import ProductionSession
from app.domain.shared.outbox import OutboxMessage
from app.domain.tournament.bracket_entities import BracketNode as DomainBracketNode
from app.domain.tournament.branding_entities import TournamentBranding as DomainBranding
from app.domain.tournament.entities import Tournament
from app.domain.tournament.team_entities import Player as DomainPlayer
from app.domain.tournament.team_entities import Team as DomainTeam
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


def _tournament_from_row(row: models.Tournament) -> Tournament:
    settings = row.settings_json if isinstance(row.settings_json, dict) else {}
    return Tournament(
        id=row.id,
        status=row.status,
        name=row.name or "",
        format=row.format or "single_elim",
        settings_json=dict(settings),
    )


def _write_tournament_row(row: models.Tournament, tournament: Tournament) -> None:
    row.status = tournament.status
    row.name = tournament.name
    row.format = tournament.format
    row.settings_json = dict(tournament.settings_json)


class SqlAlchemyTournamentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, tournament: Tournament) -> None:
        row = models.Tournament(id=tournament.id)
        _write_tournament_row(row, tournament)
        self._session.add(row)

    def get(self, tournament_id: str) -> Tournament | None:
        row = self._session.get(models.Tournament, tournament_id)
        if row is None:
            return None
        return _tournament_from_row(row)

    def save(self, tournament: Tournament) -> None:
        row = self._session.get(models.Tournament, tournament.id)
        if row is None:
            raise KeyError(f"tournament not found: {tournament.id}")
        _write_tournament_row(row, tournament)

    def list(self, *, limit: int = 100) -> list[Tournament]:
        rows = self._session.scalars(
            select(models.Tournament)
            .order_by(models.Tournament.created_at.desc())
            .limit(limit)
        ).all()
        return [_tournament_from_row(r) for r in rows]


def _team_from_row(row: models.Team) -> DomainTeam:
    return DomainTeam(
        id=row.id,
        tournament_id=row.tournament_id,
        name=row.name,
        tag=row.tag or "",
    )


def _player_from_row(row: models.Player) -> DomainPlayer:
    return DomainPlayer(
        id=row.id,
        team_id=row.team_id,
        nickname=row.nickname,
        steam_id=row.steam_id,
        is_coach=bool(row.is_coach),
    )


class SqlAlchemyTeamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, team: DomainTeam) -> None:
        self._session.add(
            models.Team(
                id=team.id,
                tournament_id=team.tournament_id,
                name=team.name,
                tag=team.tag,
            )
        )

    def get(self, team_id: str) -> DomainTeam | None:
        row = self._session.get(models.Team, team_id)
        if row is None:
            return None
        return _team_from_row(row)

    def save(self, team: DomainTeam) -> None:
        row = self._session.get(models.Team, team.id)
        if row is None:
            raise KeyError(f"team not found: {team.id}")
        row.name = team.name
        row.tag = team.tag
        row.tournament_id = team.tournament_id

    def delete(self, team_id: str) -> None:
        row = self._session.get(models.Team, team_id)
        if row is None:
            raise KeyError(f"team not found: {team_id}")
        self._session.delete(row)

    def list_for_tournament(self, tournament_id: str) -> list[DomainTeam]:
        rows = self._session.scalars(
            select(models.Team)
            .where(models.Team.tournament_id == tournament_id)
            .order_by(models.Team.created_at.asc())
        ).all()
        return [_team_from_row(r) for r in rows]

    def find_by_name(self, tournament_id: str, name: str) -> DomainTeam | None:
        row = self._session.scalars(
            select(models.Team).where(
                models.Team.tournament_id == tournament_id,
                models.Team.name == name,
            )
        ).first()
        if row is None:
            return None
        return _team_from_row(row)

    def count_for_tournament(self, tournament_id: str) -> int:
        from sqlalchemy import func

        return int(
            self._session.scalar(
                select(func.count())
                .select_from(models.Team)
                .where(models.Team.tournament_id == tournament_id)
            )
            or 0
        )


class SqlAlchemyPlayerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, player: DomainPlayer) -> None:
        self._session.add(
            models.Player(
                id=player.id,
                team_id=player.team_id,
                nickname=player.nickname,
                steam_id=player.steam_id,
                is_coach=player.is_coach,
            )
        )

    def get(self, player_id: str) -> DomainPlayer | None:
        row = self._session.get(models.Player, player_id)
        if row is None:
            return None
        return _player_from_row(row)

    def save(self, player: DomainPlayer) -> None:
        row = self._session.get(models.Player, player.id)
        if row is None:
            raise KeyError(f"player not found: {player.id}")
        row.nickname = player.nickname
        row.steam_id = player.steam_id
        row.is_coach = player.is_coach
        row.team_id = player.team_id

    def delete(self, player_id: str) -> None:
        row = self._session.get(models.Player, player_id)
        if row is None:
            raise KeyError(f"player not found: {player_id}")
        self._session.delete(row)

    def list_for_team(self, team_id: str) -> list[DomainPlayer]:
        rows = self._session.scalars(
            select(models.Player)
            .where(models.Player.team_id == team_id)
            .order_by(models.Player.created_at.asc())
        ).all()
        return [_player_from_row(r) for r in rows]

    def delete_for_team(self, team_id: str) -> None:
        rows = self._session.scalars(
            select(models.Player).where(models.Player.team_id == team_id)
        ).all()
        for row in rows:
            self._session.delete(row)

    def count_for_team(self, team_id: str) -> int:
        from sqlalchemy import func

        return int(
            self._session.scalar(
                select(func.count())
                .select_from(models.Player)
                .where(models.Player.team_id == team_id)
            )
            or 0
        )


def _bracket_from_row(row: models.BracketNode) -> DomainBracketNode:
    return DomainBracketNode(
        id=row.id,
        tournament_id=row.tournament_id,
        round=row.round,
        position=row.position,
        team_a_id=row.team_a_id,
        team_b_id=row.team_b_id,
        source_a_node_id=row.source_a_node_id,
        source_b_node_id=row.source_b_node_id,
        match_id=row.match_id,
    )


class SqlAlchemyBracketNodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, node: DomainBracketNode) -> None:
        self._session.add(
            models.BracketNode(
                id=node.id,
                tournament_id=node.tournament_id,
                round=node.round,
                position=node.position,
                team_a_id=node.team_a_id,
                team_b_id=node.team_b_id,
                source_a_node_id=node.source_a_node_id,
                source_b_node_id=node.source_b_node_id,
                match_id=node.match_id,
            )
        )

    def get(self, node_id: str) -> DomainBracketNode | None:
        row = self._session.get(models.BracketNode, node_id)
        if row is None:
            return None
        return _bracket_from_row(row)

    def save(self, node: DomainBracketNode) -> None:
        row = self._session.get(models.BracketNode, node.id)
        if row is None:
            raise KeyError(f"bracket node not found: {node.id}")
        row.team_a_id = node.team_a_id
        row.team_b_id = node.team_b_id
        row.source_a_node_id = node.source_a_node_id
        row.source_b_node_id = node.source_b_node_id
        row.match_id = node.match_id
        row.round = node.round
        row.position = node.position

    def list_for_tournament(self, tournament_id: str) -> list[DomainBracketNode]:
        rows = self._session.scalars(
            select(models.BracketNode)
            .where(models.BracketNode.tournament_id == tournament_id)
            .order_by(models.BracketNode.round.asc(), models.BracketNode.position.asc())
        ).all()
        return [_bracket_from_row(r) for r in rows]

    def delete_for_tournament(self, tournament_id: str) -> None:
        rows = self._session.scalars(
            select(models.BracketNode).where(
                models.BracketNode.tournament_id == tournament_id
            )
        ).all()
        for row in rows:
            self._session.delete(row)

    def count_for_tournament(self, tournament_id: str) -> int:
        from sqlalchemy import func

        return int(
            self._session.scalar(
                select(func.count())
                .select_from(models.BracketNode)
                .where(models.BracketNode.tournament_id == tournament_id)
            )
            or 0
        )


class SqlAlchemyBrandingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, tournament_id: str) -> DomainBranding | None:
        row = self._session.get(models.TournamentBranding, tournament_id)
        if row is None:
            return None
        colors = row.colors_json if isinstance(row.colors_json, dict) else {}
        return DomainBranding(
            tournament_id=row.tournament_id,
            colors_json=dict(colors),
            logo_blob=bytes(row.logo_blob) if row.logo_blob is not None else None,
            logo_content_type=row.logo_content_type,
            bg_blob=bytes(row.bg_blob) if row.bg_blob is not None else None,
            bg_content_type=row.bg_content_type,
        )

    def upsert(self, branding: DomainBranding) -> None:
        row = self._session.get(models.TournamentBranding, branding.tournament_id)
        if row is None:
            self._session.add(
                models.TournamentBranding(
                    tournament_id=branding.tournament_id,
                    colors_json=dict(branding.colors_json),
                    logo_blob=branding.logo_blob,
                    logo_content_type=branding.logo_content_type,
                    bg_blob=branding.bg_blob,
                    bg_content_type=branding.bg_content_type,
                )
            )
            return
        row.colors_json = dict(branding.colors_json)
        row.logo_blob = branding.logo_blob
        row.logo_content_type = branding.logo_content_type
        row.bg_blob = branding.bg_blob
        row.bg_content_type = branding.bg_content_type


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


class SqlAlchemyOverlayStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, match_id: str) -> OverlayState | None:
        row = self._session.get(models.OverlayState, match_id)
        if row is None:
            return None
        return OverlayState(
            match_id=row.match_id,
            revision=row.revision,
            scene=row.scene,
            data=dict(row.data_json or {}),
            manual_overrides=dict(row.manual_overrides or {}),
            updated_at=row.updated_at,
        )

    def add(self, state: OverlayState) -> None:
        self._session.add(
            models.OverlayState(
                match_id=state.match_id,
                revision=state.revision,
                scene=state.scene,
                data_json=state.data,
                manual_overrides=state.manual_overrides or None,
            )
        )

    def save(self, state: OverlayState) -> None:
        row = self._session.get(models.OverlayState, state.match_id)
        if row is None:
            self.add(state)
            return
        row.revision = state.revision
        row.scene = state.scene
        row.data_json = state.data
        row.manual_overrides = state.manual_overrides or None


class SqlAlchemyProductionSessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, match_id: str) -> ProductionSession | None:
        row = self._session.get(models.ProductionSession, match_id)
        if row is None:
            return None
        return ProductionSession(
            match_id=row.match_id,
            desired_scene=row.desired_scene,
            actual_scene=row.actual_scene,
            desired_stream=row.desired_stream,
            actual_stream=row.actual_stream,
            agent_status=row.agent_status,
            obs_status=row.obs_status,
            broadcast_status=row.broadcast_status,
        )

    def add(self, session: ProductionSession) -> None:
        self._session.add(
            models.ProductionSession(
                match_id=session.match_id,
                desired_scene=session.desired_scene,
                actual_scene=session.actual_scene,
                desired_stream=session.desired_stream,
                actual_stream=session.actual_stream,
                agent_status=session.agent_status,
                obs_status=session.obs_status,
                broadcast_status=session.broadcast_status,
            )
        )

    def save(self, session: ProductionSession) -> None:
        row = self._session.get(models.ProductionSession, session.match_id)
        if row is None:
            self.add(session)
            return
        row.desired_scene = session.desired_scene
        row.actual_scene = session.actual_scene
        row.desired_stream = session.desired_stream
        row.actual_stream = session.actual_stream
        row.agent_status = session.agent_status
        row.obs_status = session.obs_status
        row.broadcast_status = session.broadcast_status


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


def _invite_from_row(row: models.InviteToken) -> InviteToken:
    return InviteToken(
        id=row.id,
        token_hash=row.token_hash,
        role=row.role,
        match_id=row.match_id,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
    )


class SqlAlchemyInviteTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, invite: InviteToken) -> None:
        self._session.add(
            models.InviteToken(
                id=invite.id,
                token_hash=invite.token_hash,
                role=invite.role,
                match_id=invite.match_id,
                expires_at=invite.expires_at,
                revoked_at=invite.revoked_at,
            )
        )

    def get(self, invite_id: str) -> InviteToken | None:
        row = self._session.get(models.InviteToken, invite_id)
        if row is None:
            return None
        return _invite_from_row(row)

    def get_by_hash(self, token_hash: str) -> InviteToken | None:
        row = self._session.scalars(
            select(models.InviteToken).where(models.InviteToken.token_hash == token_hash)
        ).first()
        if row is None:
            return None
        return _invite_from_row(row)

    def save(self, invite: InviteToken) -> None:
        row = self._session.get(models.InviteToken, invite.id)
        if row is None:
            raise KeyError(f"invite not found: {invite.id}")
        row.token_hash = invite.token_hash
        row.role = invite.role
        row.match_id = invite.match_id
        row.expires_at = invite.expires_at
        row.revoked_at = invite.revoked_at


def _audit_from_row(row: models.MatchAuditLog) -> MatchAuditEntry:
    return MatchAuditEntry(
        id=row.id,
        match_id=row.match_id,
        tournament_id=row.tournament_id,
        correlation_id=row.correlation_id,
        request_id=row.request_id,
        actor_type=row.actor_type,
        actor_id=row.actor_id,
        action=row.action,
        payload=dict(row.payload or {}),
        result=row.result,
        created_at=row.created_at,
    )


class SqlAlchemyMatchAuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: MatchAuditEntry) -> None:
        self._session.add(
            models.MatchAuditLog(
                id=entry.id,
                match_id=entry.match_id,
                tournament_id=entry.tournament_id,
                correlation_id=entry.correlation_id,
                request_id=entry.request_id,
                actor_type=entry.actor_type,
                actor_id=entry.actor_id,
                action=entry.action,
                payload=entry.payload,
                result=entry.result,
            )
        )

    def list_for_match(
        self,
        match_id: str,
        *,
        limit: int = 50,
    ) -> list[MatchAuditEntry]:
        rows = self._session.scalars(
            select(models.MatchAuditLog)
            .where(models.MatchAuditLog.match_id == match_id)
            .order_by(models.MatchAuditLog.created_at.desc())
            .limit(max(1, min(limit, 200)))
        ).all()
        return [_audit_from_row(row) for row in rows]
