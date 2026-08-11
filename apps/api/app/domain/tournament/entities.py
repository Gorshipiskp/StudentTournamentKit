"""Domain entities — tournament (no SQLAlchemy / FastAPI)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tournament:
    id: str
    status: str = "draft"
