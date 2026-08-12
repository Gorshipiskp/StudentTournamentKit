"""Identity repository ports."""

from __future__ import annotations

from typing import Protocol

from app.domain.identity.entities import InviteToken


class InviteTokenRepository(Protocol):
    def add(self, invite: InviteToken) -> None: ...

    def get(self, invite_id: str) -> InviteToken | None: ...

    def get_by_hash(self, token_hash: str) -> InviteToken | None: ...

    def save(self, invite: InviteToken) -> None: ...
