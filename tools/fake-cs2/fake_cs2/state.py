"""In-memory match state for Fake Game Server."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


@dataclass
class CommandRecord:
    command_id: str
    type: str
    status: str
    timestamp: str
    error: str | None = None
    result: dict[str, Any] | None = None


@dataclass
class MatchState:
    match_id: str
    server_id: str
    map_name: str = "de_mirage"
    round: int = 0
    score_a: int = 0
    score_b: int = 0
    phase: str = "warmup"
    paused: bool = False
    loaded: bool = False
    completed: bool = False
    last_sequence: int = 0
    players: list[dict[str, Any]] = field(default_factory=list)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _acks: dict[str, CommandRecord] = field(default_factory=dict, repr=False)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "match_id": self.match_id,
                "server_id": self.server_id,
                "map": self.map_name,
                "round": self.round,
                "score": {"team_a": self.score_a, "team_b": self.score_b},
                "phase": self.phase,
                "paused": self.paused,
                "loaded": self.loaded,
                "completed": self.completed,
                "last_sequence": self.last_sequence,
                "players": list(self.players),
            }

    def next_sequence(self) -> int:
        with self._lock:
            self.last_sequence += 1
            return self.last_sequence

    def get_ack(self, command_id: str) -> CommandRecord | None:
        with self._lock:
            return self._acks.get(command_id)

    def store_ack(self, record: CommandRecord) -> CommandRecord:
        with self._lock:
            existing = self._acks.get(record.command_id)
            if existing is not None:
                return existing
            self._acks[record.command_id] = record
            return record

    def apply_command(
        self,
        *,
        command_id: str,
        command_type: str,
        payload: dict[str, Any] | None = None,
    ) -> CommandRecord:
        payload = payload or {}
        with self._lock:
            existing = self._acks.get(command_id)
            if existing is not None:
                return CommandRecord(
                    command_id=existing.command_id,
                    type=existing.type,
                    status="duplicate",
                    timestamp=utc_now_iso(),
                    error=None,
                    result=existing.result,
                )

            ts = utc_now_iso()
            try:
                result = self._apply_unlocked(command_type, payload)
            except ValueError as exc:
                record = CommandRecord(
                    command_id=command_id,
                    type=command_type,
                    status="failed",
                    timestamp=ts,
                    error=str(exc),
                    result=None,
                )
                self._acks[command_id] = record
                return record

            record = CommandRecord(
                command_id=command_id,
                type=command_type,
                status="confirmed",
                timestamp=ts,
                error=None,
                result=result,
            )
            self._acks[command_id] = record
            return record

    def _apply_unlocked(
        self, command_type: str, payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        if command_type == "LoadMatch":
            if self.completed:
                raise ValueError("match already completed")
            self.map_name = str(payload.get("map", self.map_name))
            self.loaded = True
            self.phase = "warmup"
            self.round = 0
            self.score_a = 0
            self.score_b = 0
            self.paused = False
            self.completed = False
            return {"loaded": True, "map": self.map_name}

        if command_type == "PauseMatch":
            if not self.loaded:
                raise ValueError("match not loaded")
            if self.completed:
                raise ValueError("match already completed")
            self.paused = True
            return {"paused": True}

        if command_type == "ResumeMatch":
            if not self.loaded:
                raise ValueError("match not loaded")
            self.paused = False
            return {"paused": False}

        if command_type == "ForfeitMatch":
            if not self.loaded:
                raise ValueError("match not loaded")
            losing = payload.get("losing_team")
            if losing not in {"team_a", "team_b"}:
                raise ValueError("losing_team must be team_a or team_b")
            # Winner gets enough rounds to look finished (simple stub).
            if losing == "team_a":
                self.score_b = max(self.score_b, 13)
            else:
                self.score_a = max(self.score_a, 13)
            self.paused = False
            self.completed = True
            self.phase = "ended"
            return {
                "completed": True,
                "losing_team": losing,
                "score": {"team_a": self.score_a, "team_b": self.score_b},
            }

        if command_type == "GetSnapshot":
            return {"snapshot": self.snapshot()}

        raise ValueError(f"unknown command type: {command_type}")

    def start_round(self, *, phase: str = "buy") -> dict[str, Any]:
        with self._lock:
            if not self.loaded:
                raise ValueError("match not loaded")
            if self.completed:
                raise ValueError("match completed")
            if self.paused:
                raise ValueError("match paused")
            self.round += 1
            self.phase = phase
            return {"round": self.round, "phase": self.phase}

    def end_round(self, *, winner: str) -> dict[str, Any]:
        with self._lock:
            if not self.loaded:
                raise ValueError("match not loaded")
            if self.completed:
                raise ValueError("match completed")
            if self.paused:
                raise ValueError("match paused")
            if winner == "team_a":
                self.score_a += 1
            elif winner == "team_b":
                self.score_b += 1
            else:
                raise ValueError("winner must be team_a or team_b")
            self.phase = "freeze"
            return {
                "round": self.round,
                "score": {"team_a": self.score_a, "team_b": self.score_b},
                "map": self.map_name,
                "winner": winner,
            }

    def mark_tech_pause(self, started: bool) -> None:
        with self._lock:
            self.paused = started

    @staticmethod
    def new_event_id() -> str:
        return str(uuid4())
