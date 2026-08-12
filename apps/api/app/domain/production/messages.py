"""Production WS / HTTP message shapes (no OBS SDK types)."""

from __future__ import annotations

from typing import Any

from app.domain.production.entities import ProductionSession

PROTOCOL_VERSION = 1

TYPE_AGENT_HELLO = "agent.hello"
TYPE_AGENT_PING = "agent.ping"
TYPE_AGENT_PONG = "agent.pong"
TYPE_PRODUCTION_DESIRED = "production.desired"
TYPE_PRODUCTION_ACTUAL = "production.actual"

ALLOWED_SCENES = frozenset(
    {"waiting", "intro", "teams", "ingame", "break", "winner"}
)
ALLOWED_STREAMS = frozenset({"off", "on"})


def desired_message(session: ProductionSession) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_VERSION,
        "type": TYPE_PRODUCTION_DESIRED,
        "match_id": session.match_id,
        "desired": {
            "scene": session.desired_scene,
            "stream": session.desired_stream,
        },
    }


def actual_ack_message(session: ProductionSession) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_VERSION,
        "type": "production.actual_ack",
        "match_id": session.match_id,
        "actual": {
            "scene": session.actual_scene,
            "stream": session.actual_stream,
        },
        "agent_status": session.agent_status,
        "obs_status": session.obs_status,
        "broadcast_status": session.broadcast_status,
    }
