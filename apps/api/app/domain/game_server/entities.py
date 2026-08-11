"""Game server registry entity (CS2 VPS / Fake)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

SERVER_AVAILABLE = "available"
SERVER_ASSIGNED = "assigned"
SERVER_OFFLINE = "offline"
SERVER_DRAINING = "draining"


@dataclass
class GameServer:
    id: str
    status: str = SERVER_AVAILABLE
    host: str | None = None
    port: int | None = None
    endpoint_url: str | None = None
    webhook_secret: str | None = None
    assigned_match_id: str | None = None
    last_heartbeat: datetime | None = None
    bridge_version: str | None = None
    protocol_version: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "host": self.host,
            "port": self.port,
            "endpoint_url": self.endpoint_url,
            "assigned_match_id": self.assigned_match_id,
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
            "bridge_version": self.bridge_version,
            "protocol_version": self.protocol_version,
            "has_webhook_secret": bool(self.webhook_secret),
        }
