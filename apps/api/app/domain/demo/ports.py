"""Demo ports."""

from __future__ import annotations

from typing import Protocol

from app.domain.demo.entities import DemoFile


class DemoFileRepository(Protocol):
    def add(self, demo: DemoFile) -> None: ...

    def list_for_match(self, match_id: str) -> list[DemoFile]: ...
