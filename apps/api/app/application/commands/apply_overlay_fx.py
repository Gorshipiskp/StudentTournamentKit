"""Push ephemeral overlay FX (lab / director smoke) without CS2 events."""

from __future__ import annotations

from typing import Any

from app.application.commands.rebuild_overlay import rebuild_overlay_snapshot
from app.application.unit_of_work import UnitOfWork
from app.domain.overlay.live_fx import FX_EVENT_TYPES, build_live_fx

# Client-facing kind → ingest event_type for build_live_fx
_KIND_TO_EVENT: dict[str, str] = {
    "round_win": "round_end",
    "round_end": "round_end",
    "bomb_planted": "bomb_planted",
    "bomb_defusing": "bomb_defuse_start",
    "bomb_defuse_start": "bomb_defuse_start",
    "bomb_defused": "bomb_defused",
    "bomb_exploded": "bomb_exploded",
}


def apply_overlay_fx(
    uow: UnitOfWork,
    *,
    match_id: str,
    kind: str | None = None,
    side: str | None = None,
    site: int | str | None = None,
    round_number: int | None = None,
    timer_sec: int | None = None,
    has_kit: bool | None = None,
    clear: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Inject or clear overlay `data.fx`; bumps revision and notifies WS."""
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")

    if clear:
        return rebuild_overlay_snapshot(
            uow,
            match,
            correlation_id=correlation_id,
            notify=True,
            clear_fx=True,
        )

    if not kind:
        raise ValueError("kind required unless clear=true")

    key = kind.strip().lower()
    event_type = _KIND_TO_EVENT.get(key)
    if event_type is None or event_type not in FX_EVENT_TYPES:
        allowed = ", ".join(sorted(_KIND_TO_EVENT))
        raise ValueError(f"unknown fx kind: {kind}. Allowed: {allowed}")

    payload: dict[str, Any] = {}
    if side in {"team_a", "team_b", "ct", "t"}:
        payload["winner"] = {"ct": "team_a", "t": "team_b"}.get(side, side)
        payload["side"] = payload["winner"]
    if site is not None:
        payload["site"] = site
    if round_number is not None:
        payload["round"] = int(round_number)
    if timer_sec is not None:
        payload["timer_sec"] = int(timer_sec)
    if has_kit is not None:
        payload["has_kit"] = bool(has_kit)

    overlay = uow.overlays.get(match_id)
    seq = (overlay.revision if overlay else 0) + 1
    fx = build_live_fx(event_type, payload, sequence=seq)
    if fx is None:
        raise ValueError(f"fx builder returned nothing for {event_type}")

    return rebuild_overlay_snapshot(
        uow,
        match,
        correlation_id=correlation_id,
        notify=True,
        live_fx=fx,
    )
