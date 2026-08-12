"""Production ports."""

from __future__ import annotations

from typing import Protocol

from app.domain.production.entities import ProductionSession


class ProductionSessionRepository(Protocol):
    def get(self, match_id: str) -> ProductionSession | None: ...

    def add(self, session: ProductionSession) -> None: ...

    def save(self, session: ProductionSession) -> None: ...
