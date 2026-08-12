"""Match audit log repository port."""

from __future__ import annotations

from typing import Protocol

from app.domain.audit.entities import MatchAuditEntry


class MatchAuditLogRepository(Protocol):
    def add(self, entry: MatchAuditEntry) -> None: ...

    def list_for_match(
        self,
        match_id: str,
        *,
        limit: int = 50,
    ) -> list[MatchAuditEntry]: ...
