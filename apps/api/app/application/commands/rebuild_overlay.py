"""Rebuild overlay snapshot from match + production; bump overlay_revision."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.application.commands.write_audit import write_audit
from app.domain.audit.entities import ACTION_DIRECTOR_SCORE_OVERRIDE, ACTOR_DIRECTOR
from app.domain.match.entities import Match
from app.domain.overlay.entities import OVERLAY_UPDATED, OverlayState
from app.domain.overlay.merge_policy import merge_overlay_data
from app.domain.production.entities import ProductionSession, SCENE_WAITING
from app.domain.shared.outbox import OutboxMessage


def seed_overlay_and_production(uow: UnitOfWork, match: Match) -> OverlayState:
    """Initial rows on match create (revision=1). Caller commits."""
    existing = uow.overlays.get(match.id)
    if existing is not None:
        _ensure_production(uow, match.id)
        return existing
    return _persist_snapshot(
        uow,
        match,
        revision=1,
        notify=False,
        correlation_id=None,
    )


def rebuild_overlay_snapshot(
    uow: UnitOfWork,
    match: Match,
    *,
    correlation_id: str | None = None,
    notify: bool = True,
    live_fx: dict[str, Any] | None = None,
    clear_fx: bool = False,
) -> dict[str, Any]:
    """
    Merge → bump revision → persist → optional outbox overlay.updated.
    Returns WS/HTTP message dict.

    live_fx: ephemeral CS2 chrome (bomb / round). If omitted, previous fx is kept
    unless clear_fx=True.
    """
    existing = uow.overlays.get(match.id)
    revision = (existing.revision if existing else 0) + 1
    state = _persist_snapshot(
        uow,
        match,
        revision=revision,
        notify=notify,
        correlation_id=correlation_id,
        previous=existing,
        live_fx=live_fx,
        clear_fx=clear_fx,
    )
    return state.to_message()


def get_overlay_message(uow: UnitOfWork, match_id: str) -> dict[str, Any] | None:
    match = uow.matches.get(match_id)
    if match is None:
        return None
    state = uow.overlays.get(match_id)
    if state is None:
        state = seed_overlay_and_production(uow, match)
    return state.to_message()


_ALLOWED_OVERRIDE_KEYS = frozenset(
    {
        "team_a_name",
        "team_b_name",
        "score_team_a",
        "score_team_b",
        "map",
        "round",
        "judge_banner",
    }
)


def apply_overlay_override(
    uow: UnitOfWork,
    *,
    match_id: str,
    patch: dict[str, Any] | None = None,
    clear: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Merge manual override fields → bump overlay revision + notify WS."""
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")

    existing = uow.overlays.get(match_id)
    if existing is None:
        seed_overlay_and_production(uow, match)
        existing = uow.overlays.get(match_id)
    assert existing is not None

    if clear:
        existing.manual_overrides = {}
    else:
        patch = patch or {}
        unknown = set(patch) - _ALLOWED_OVERRIDE_KEYS
        if unknown:
            raise ValueError(f"unknown override keys: {sorted(unknown)}")
        merged = dict(existing.manual_overrides)
        for key, value in patch.items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        existing.manual_overrides = merged

    uow.overlays.save(existing)
    write_audit(
        uow,
        match_id=match_id,
        action=ACTION_DIRECTOR_SCORE_OVERRIDE,
        actor_type=ACTOR_DIRECTOR,
        tournament_id=match.tournament_id,
        payload={"clear": clear, "fields": sorted((patch or {}).keys()) if not clear else []},
        correlation_id=correlation_id,
    )
    return rebuild_overlay_snapshot(
        uow,
        match,
        correlation_id=correlation_id,
        notify=True,
    )


def _ensure_production(uow: UnitOfWork, match_id: str) -> ProductionSession:
    production = uow.production.get(match_id)
    if production is not None:
        return production
    production = ProductionSession(match_id=match_id)
    uow.production.add(production)
    flush = getattr(uow, "flush", None)
    if callable(flush):
        flush()
    return production


def _branding_for_match(uow: UnitOfWork, match: Match) -> dict[str, Any] | None:
    branding = uow.branding.get(match.tournament_id)
    if branding is None:
        return None
    payload = branding.to_overlay_branding()
    # Omit empty branding object (no colors, no assets)
    if not payload.get("logo_url") and not payload.get("bg_url") and not payload.get("colors"):
        return None
    return payload


def _tournament_name(uow: UnitOfWork, match: Match) -> str | None:
    tournament = uow.tournaments.get(match.tournament_id)
    if tournament is None:
        return None
    name = (tournament.name or "").strip()
    return name or None


def _persist_snapshot(
    uow: UnitOfWork,
    match: Match,
    *,
    revision: int,
    notify: bool,
    correlation_id: str | None,
    previous: OverlayState | None = None,
    live_fx: dict[str, Any] | None = None,
    clear_fx: bool = False,
) -> OverlayState:
    production = _ensure_production(uow, match.id)

    overrides = dict(previous.manual_overrides) if previous else {}
    if previous is None:
        current = uow.overlays.get(match.id)
        if current is not None:
            overrides = dict(current.manual_overrides)
            previous = current

    fx: dict[str, Any] | None = None
    if clear_fx:
        fx = None
    elif live_fx is not None:
        fx = live_fx
    elif previous and isinstance(previous.data.get("fx"), dict):
        fx = dict(previous.data["fx"])

    data = merge_overlay_data(
        match_public=match.to_public_dict(),
        desired_scene=production.desired_scene or SCENE_WAITING,
        manual_overrides=overrides,
        branding=_branding_for_match(uow, match),
        tournament_name=_tournament_name(uow, match),
        live_fx=fx,
    )
    state = OverlayState(
        match_id=match.id,
        revision=revision,
        scene=str(data["scene"]),
        data=data,
        manual_overrides=overrides,
    )
    if uow.overlays.get(match.id) is None:
        uow.overlays.add(state)
    else:
        uow.overlays.save(state)

    if notify:
        uow.outbox.add(
            OutboxMessage(
                id=str(uuid4()),
                event_type=OVERLAY_UPDATED,
                aggregate_type="overlay",
                aggregate_id=match.id,
                payload={"message": state.to_message()},
                correlation_id=correlation_id,
            )
        )
    return state
