"""Update production desired state + outbox notify agent/overlay."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.rebuild_overlay import (
    rebuild_overlay_snapshot,
    seed_overlay_and_production,
)
from app.application.commands.write_audit import write_audit
from app.application.unit_of_work import UnitOfWork
from app.domain.audit.entities import (
    ACTION_DIRECTOR_SCENE_CHANGE,
    ACTOR_DIRECTOR,
)
from app.domain.production.entities import PRODUCTION_DESIRED_CHANGED
from app.domain.production.messages import (
    ALLOWED_SCENES,
    ALLOWED_STREAMS,
    desired_message,
)
from app.domain.shared.outbox import OutboxMessage


class ProductionConflict(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def get_production(uow: UnitOfWork, *, match_id: str) -> dict[str, Any]:
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    session = uow.production.get(match_id)
    if session is None:
        seed_overlay_and_production(uow, match)
        session = uow.production.get(match_id)
    assert session is not None
    return session.to_public_dict()


def patch_production(
    uow: UnitOfWork,
    *,
    match_id: str,
    desired_scene: str | None = None,
    desired_stream: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Persist desired changes; enqueue agent notify; rebuild overlay if scene changes."""
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")

    session = uow.production.get(match_id)
    if session is None:
        seed_overlay_and_production(uow, match)
        session = uow.production.get(match_id)
    assert session is not None

    if desired_scene is None and desired_stream is None:
        raise ProductionConflict("no fields to patch")

    scene_changed = False
    previous_scene = session.desired_scene
    if desired_scene is not None:
        if desired_scene not in ALLOWED_SCENES:
            raise ProductionConflict(
                f"invalid desired_scene: {desired_scene}; "
                f"allowed={sorted(ALLOWED_SCENES)}"
            )
        if desired_scene != session.desired_scene:
            session.desired_scene = desired_scene
            scene_changed = True

    if desired_stream is not None:
        if desired_stream not in ALLOWED_STREAMS:
            raise ProductionConflict(
                f"invalid desired_stream: {desired_stream}; "
                f"allowed={sorted(ALLOWED_STREAMS)}"
            )
        session.desired_stream = desired_stream

    uow.production.save(session)

    uow.outbox.add(
        OutboxMessage(
            id=str(uuid4()),
            event_type=PRODUCTION_DESIRED_CHANGED,
            aggregate_type="production",
            aggregate_id=match_id,
            payload={"message": desired_message(session)},
            correlation_id=correlation_id,
        )
    )

    if scene_changed:
        write_audit(
            uow,
            match_id=match_id,
            action=ACTION_DIRECTOR_SCENE_CHANGE,
            actor_type=ACTOR_DIRECTOR,
            tournament_id=match.tournament_id,
            payload={"from": previous_scene, "to": desired_scene},
            correlation_id=correlation_id,
        )
        rebuild_overlay_snapshot(
            uow,
            match,
            correlation_id=correlation_id,
            notify=True,
        )

    return session.to_public_dict()


def apply_agent_actual(
    uow: UnitOfWork,
    *,
    match_id: str,
    actual_scene: str | None = None,
    actual_stream: str | None = None,
    obs_status: str | None = None,
    broadcast_status: str | None = None,
    agent_status: str | None = None,
) -> dict[str, Any]:
    """Agent reports observed OBS/production actual (no command replay)."""
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    session = uow.production.get(match_id)
    if session is None:
        seed_overlay_and_production(uow, match)
        session = uow.production.get(match_id)
    assert session is not None

    if actual_scene is not None:
        if actual_scene not in ALLOWED_SCENES:
            raise ProductionConflict(f"invalid actual_scene: {actual_scene}")
        session.actual_scene = actual_scene
    if actual_stream is not None:
        if actual_stream not in {"off", "on", "unknown"}:
            raise ProductionConflict(f"invalid actual_stream: {actual_stream}")
        session.actual_stream = actual_stream
    if obs_status is not None:
        session.obs_status = obs_status
    if broadcast_status is not None:
        session.broadcast_status = broadcast_status
    if agent_status is not None:
        session.agent_status = agent_status

    uow.production.save(session)
    return session.to_public_dict()


def set_agent_connection_status(
    uow: UnitOfWork,
    *,
    match_id: str,
    agent_status: str,
) -> None:
    match = uow.matches.get(match_id)
    if match is None:
        return
    session = uow.production.get(match_id)
    if session is None:
        seed_overlay_and_production(uow, match)
        session = uow.production.get(match_id)
    if session is None:
        return
    session.agent_status = agent_status
    uow.production.save(session)
