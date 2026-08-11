"""Demo file metadata — durable URI after match (ADR-034)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DemoFile:
    id: str
    match_id: str
    durable_uri: str
    size_bytes: int = 0
    map_name: str | None = None
    source_uri: str | None = None
    created_at: datetime | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "durable_uri": self.durable_uri,
            "size_bytes": self.size_bytes,
            "map_name": self.map_name,
            "source_uri": self.source_uri,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
