"""Overlay ports."""

from __future__ import annotations

from typing import Protocol

from app.domain.overlay.entities import OverlayState


class OverlayStateRepository(Protocol):
    def get(self, match_id: str) -> OverlayState | None: ...

    def add(self, state: OverlayState) -> None: ...

    def save(self, state: OverlayState) -> None: ...
