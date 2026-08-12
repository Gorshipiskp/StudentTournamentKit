"""Domain entities — tournament (no SQLAlchemy / FastAPI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_COMPLETED = "completed"

FORMAT_SINGLE_ELIM = "single_elim"

ALLOWED_STATUSES = frozenset({STATUS_DRAFT, STATUS_PUBLISHED, STATUS_COMPLETED})
ALLOWED_FORMATS = frozenset({FORMAT_SINGLE_ELIM})


@dataclass
class Tournament:
    id: str
    status: str = STATUS_DRAFT
    name: str = ""
    format: str = FORMAT_SINGLE_ELIM
    settings_json: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "format": self.format,
            "status": self.status,
            "settings": dict(self.settings_json),
        }
