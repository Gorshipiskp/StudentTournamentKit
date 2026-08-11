"""Ports for tournament persistence."""

from __future__ import annotations

from typing import Protocol

from app.domain.tournament.entities import Tournament


class TournamentRepository(Protocol):
    def add(self, tournament: Tournament) -> None: ...

    def get(self, tournament_id: str) -> Tournament | None: ...
