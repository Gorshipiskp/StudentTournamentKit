"""Ports for game server registry."""

from __future__ import annotations

from typing import Protocol

from app.domain.game_server.entities import GameServer


class GameServerRepository(Protocol):
    def add(self, server: GameServer) -> None: ...

    def get(self, server_id: str) -> GameServer | None: ...

    def save(self, server: GameServer) -> None: ...

    def list(self, *, limit: int = 100) -> list[GameServer]: ...
