"""Fake / platform match start (no live CS2 VPS required)."""

from __future__ import annotations

from typing import Any

from app.application.commands.rebuild_overlay import rebuild_overlay_snapshot
from app.application.commands.update_production import patch_production
from app.application.unit_of_work import UnitOfWork
from app.domain.match.entities import (
    MATCH_CANCELLED,
    MATCH_COMPLETED,
    MATCH_FORFEITED,
    MATCH_LIVE,
    MATCH_SCHEDULED,
    MATCH_SERVER_ASSIGNED,
    MATCH_WARMUP,
)
from app.domain.production.entities import SCENE_INGAME

_TERMINAL = frozenset({MATCH_COMPLETED, MATCH_FORFEITED, MATCH_CANCELLED})
_STARTABLE = frozenset(
    {MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED, MATCH_WARMUP, MATCH_LIVE}
)


class MatchStartError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def start_match_fake(
    uow: UnitOfWork,
    *,
    match_id: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Mark match live for Fake / admin path (GATE without CS2 VPS).

    Sets game_server_id=srv_fake if unset, scene=ingame, rebuilds overlay.
    Idempotent if already live.
    """
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    if match.status in _TERMINAL:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="terminal",
        )
    if match.status not in _STARTABLE and match.status != MATCH_LIVE:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="bad_status",
        )

    already = match.status == MATCH_LIVE
    if not already:
        match.status = MATCH_LIVE
        match.phase = "live"
        if not match.game_server_id:
            match.game_server_id = "srv_fake"
        if not match.map_name:
            match.map_name = "de_mirage"
        uow.matches.save(match)

    patch_production(
        uow,
        match_id=match.id,
        desired_scene=SCENE_INGAME,
        correlation_id=correlation_id,
    )
    # patch_production already rebuilds overlay when scene changes
    if already:
        rebuild_overlay_snapshot(uow, match, correlation_id=correlation_id, notify=True)

    uow.commit()
    refreshed = uow.matches.get(match_id)
    assert refreshed is not None
    return {
        "match": refreshed.to_public_dict(),
        "mode": "fake",
        "note": "Fake start: без live CS2 VPS; для live сервера используйте Bridge/ingest.",
        "already_live": already,
    }
