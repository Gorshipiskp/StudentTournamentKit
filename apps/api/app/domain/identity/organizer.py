"""Organizer session (instance-per-organizer; env bootstrap)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ROLE_ORGANIZER = "organizer"


@dataclass(frozen=True)
class OrganizerSession:
    role: str
    expires_at: datetime

    def is_organizer(self) -> bool:
        return self.role == ROLE_ORGANIZER
