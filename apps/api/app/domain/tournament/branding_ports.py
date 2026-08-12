"""Ports for tournament branding."""

from __future__ import annotations

from typing import Protocol

from app.domain.tournament.branding_entities import TournamentBranding


class BrandingRepository(Protocol):
    def get(self, tournament_id: str) -> TournamentBranding | None: ...

    def upsert(self, branding: TournamentBranding) -> None: ...
