"""Overlay domain — full snapshot merge (no OBS/WS types)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PROTOCOL_VERSION = 1
OVERLAY_SNAPSHOT_TYPE = "overlay.snapshot"
OVERLAY_UPDATED = "overlay.updated"

DEFAULT_TEAM_A_NAME = "Team A"
DEFAULT_TEAM_B_NAME = "Team B"
WATERMARK_TEXT = "STP"


@dataclass
class OverlayState:
    """Durable overlay revision per match."""

    match_id: str
    revision: int
    scene: str
    data: dict[str, Any]
    manual_overrides: dict[str, Any] = field(default_factory=dict)

    def to_message(self) -> dict[str, Any]:
        return {
            "protocol": PROTOCOL_VERSION,
            "type": OVERLAY_SNAPSHOT_TYPE,
            "match_id": self.match_id,
            "version": self.revision,
            "data": dict(self.data),
        }
