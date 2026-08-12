"""Minimal platform-owned tables (SQLAlchemy 2)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, func
from sqlalchemy.dialects.mysql import JSON, MEDIUMBLOB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.base import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="single_elim")
    settings_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tournaments.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    review_resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    score_team_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_team_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    map_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="warmup")
    game_server_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reconcile_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    actual_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    desired_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    game_endpoint_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class GameEvent(Base):
    """Transport dedup store — event_id UNIQUE (= PK)."""

    __tablename__ = "game_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    server_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class GameCommand(Base):
    __tablename__ = "game_commands"

    command_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )
    command_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="requested")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ack_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ack_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ack_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GameServer(Base):
    __tablename__ = "game_servers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    endpoint_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_match_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bridge_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    protocol_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DemoFile(Base):
    __tablename__ = "demo_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )
    durable_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    map_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class OverlayState(Base):
    __tablename__ = "overlay_states"

    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        primary_key=True,
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scene: Mapped[str] = mapped_column(String(32), nullable=False, default="waiting")
    data_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    manual_overrides: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ProductionSession(Base):
    __tablename__ = "production_sessions"

    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        primary_key=True,
    )
    desired_scene: Mapped[str] = mapped_column(String(32), nullable=False, default="waiting")
    actual_scene: Mapped[str | None] = mapped_column(String(32), nullable=True)
    desired_stream: Mapped[str] = mapped_column(String(16), nullable=False, default="off")
    actual_stream: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    agent_status: Mapped[str] = mapped_column(String(32), nullable=False, default="disconnected")
    obs_status: Mapped[str] = mapped_column(String(32), nullable=False, default="disconnected")
    broadcast_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    match_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matches.id"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tournaments.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    tag: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    team_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    steam_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_coach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TournamentBranding(Base):
    __tablename__ = "tournament_branding"

    tournament_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tournaments.id"),
        primary_key=True,
    )
    logo_blob: Mapped[bytes | None] = mapped_column(
        LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
        nullable=True,
    )
    logo_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bg_blob: Mapped[bytes | None] = mapped_column(
        LargeBinary().with_variant(MEDIUMBLOB(), "mysql"),
        nullable=True,
    )
    bg_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    colors_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BracketNode(Base):
    __tablename__ = "bracket_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tournaments.id"),
        nullable=False,
        index=True,
    )
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    team_a_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("teams.id"), nullable=True
    )
    team_b_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("teams.id"), nullable=True
    )
    source_a_node_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_b_node_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    match_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("matches.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
