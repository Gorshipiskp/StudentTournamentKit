"""Ports for bracket_nodes."""

from __future__ import annotations

from typing import Protocol

from app.domain.tournament.bracket_entities import BracketNode


class BracketNodeRepository(Protocol):
    def add(self, node: BracketNode) -> None: ...

    def get(self, node_id: str) -> BracketNode | None: ...

    def save(self, node: BracketNode) -> None: ...

    def list_for_tournament(self, tournament_id: str) -> list[BracketNode]: ...

    def delete_for_tournament(self, tournament_id: str) -> None: ...

    def count_for_tournament(self, tournament_id: str) -> int: ...
