"""Normalized CS2↔Platform shapes (no MatchZy / RCON types).

Canon: infra/game-server/CONTRACT.md · INVARIANTS §6 · ARCHITECTURE §11.
Ingest wiring lands in TZ002 P2; Fake uses the same field names.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

PROTOCOL_VERSION = "1"

EventType = Literal[
    "match_loaded",
    "round_start",
    "round_end",
    "score_changed",
    "tech_pause_started",
    "tech_pause_ended",
    "match_completed",
    "heartbeat",
]

CommandType = Literal[
    "LoadMatch",
    "PauseMatch",
    "ResumeMatch",
    "ForfeitMatch",
    "GetSnapshot",
]

CommandAckStatus = Literal["accepted", "confirmed", "failed", "duplicate"]

Phase = Literal["warmup", "buy", "live", "freeze", "overtime", "ended"]


class ScoreDict(TypedDict):
    team_a: int
    team_b: int


class GameEventDict(TypedDict):
    event_id: str
    sequence: int
    server_id: str
    match_id: str
    type: str
    timestamp: str
    correlation_id: str | None
    payload: dict[str, Any]


class GameSnapshotDict(TypedDict):
    match_id: str
    server_id: str
    map: str
    round: int
    score: ScoreDict
    phase: str
    paused: bool
    loaded: bool
    completed: bool
    last_sequence: int
    players: list[dict[str, Any]]


class CommandRequestDict(TypedDict):
    command_id: str
    type: str
    match_id: str
    server_id: str
    timestamp: str
    correlation_id: str | None
    payload: dict[str, Any]


class CommandAckDict(TypedDict):
    command_id: str
    type: str
    status: str
    timestamp: str
    error: str | None
    result: dict[str, Any] | None
