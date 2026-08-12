"""Production session — desired vs actual (no OBS protocol types)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCENE_WAITING = "waiting"
SCENE_INTRO = "intro"
SCENE_TEAMS = "teams"
SCENE_INGAME = "ingame"
SCENE_BREAK = "break"
SCENE_WINNER = "winner"

AGENT_DISCONNECTED = "disconnected"
AGENT_CONNECTED = "connected"
AGENT_DEGRADED = "degraded"

OBS_DISCONNECTED = "disconnected"
OBS_CONNECTED = "connected"

STREAM_OFF = "off"
STREAM_ON = "on"
STREAM_UNKNOWN = "unknown"

BROADCAST_UNKNOWN = "unknown"
BROADCAST_IDLE = "idle"
BROADCAST_STREAMING = "streaming"

PRODUCTION_DESIRED_CHANGED = "production.desired_changed"


@dataclass
class ProductionSession:
    match_id: str
    desired_scene: str = SCENE_WAITING
    actual_scene: str | None = None
    desired_stream: str = STREAM_OFF
    actual_stream: str = STREAM_UNKNOWN
    agent_status: str = AGENT_DISCONNECTED
    obs_status: str = OBS_DISCONNECTED
    broadcast_status: str = BROADCAST_UNKNOWN

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "desired": {
                "scene": self.desired_scene,
                "stream": self.desired_stream,
            },
            "actual": {
                "scene": self.actual_scene,
                "stream": self.actual_stream,
            },
            "agent_status": self.agent_status,
            "obs_status": self.obs_status,
            "broadcast_status": self.broadcast_status,
        }
