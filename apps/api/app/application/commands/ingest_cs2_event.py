"""Ingest normalized CS2 event → Match + event_id dedup + outbox."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.application.commands.finalize_demo import finalize_match_demo
from app.application.commands.judge_review import (
    mark_review_paused_if_pending,
    maybe_arm_pause_on_round_start,
    notify_review_status,
)
from app.application.commands.rebuild_overlay import rebuild_overlay_snapshot
from app.application.unit_of_work import UnitOfWork
from app.domain.match.apply import apply_game_event
from app.domain.match.events import (
    MATCH_RECONCILE_NEEDED,
    MATCH_SCORE_UPDATED,
    MATCH_STATUS_CHANGED,
)
from app.domain.match.messages import JUDGE_REVIEW_TECH_PAUSE
from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.adapters.cs2.command_client import GameCommandTransport


def ingest_cs2_event(
    uow: UnitOfWork,
    *,
    event_id: str,
    sequence: int,
    server_id: str,
    match_id: str,
    event_type: str,
    payload: dict[str, Any],
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
) -> dict[str, Any]:
    """Apply one game event inside caller's UoW transaction (caller commits)."""
    if uow.game_events.exists(event_id):
        match = uow.matches.get(match_id)
        return {
            "status": "duplicate",
            "event_id": event_id,
            "match_id": match_id,
            "applied": False,
            "match": match.to_public_dict() if match else None,
        }

    match = uow.matches.get(match_id)
    if match is None:
        return {
            "status": "not_found",
            "event_id": event_id,
            "match_id": match_id,
            "applied": False,
            "match": None,
        }

    uow.game_events.add(
        event_id=event_id,
        match_id=match_id,
        sequence=sequence,
        event_type=event_type,
        server_id=server_id,
        payload=payload,
    )

    result = apply_game_event(
        match,
        event_type=event_type,
        sequence=sequence,
        payload=payload,
        server_id=server_id,
    )

    armed_pause: dict[str, Any] | None = None
    out_demo: dict[str, Any] | None = None
    review_pause_synced = False
    if result.applied:
        if event_type == "tech_pause_started":
            review_pause_synced = mark_review_paused_if_pending(match)
        if event_type == "round_start":
            phase = payload.get("phase") if isinstance(payload.get("phase"), str) else None
            armed_pause = maybe_arm_pause_on_round_start(
                uow,
                match,
                phase=phase,
                correlation_id=correlation_id,
                transport=transport,
            )
            match = uow.matches.get(match_id) or match
        if event_type == "heartbeat":
            _touch_server_heartbeat(uow, match, payload)
        if event_type == "match_completed" and not uow.demos.list_for_match(match.id):
            source = payload.get("demo_path") or payload.get("source_demo_path")
            if not isinstance(source, str):
                source = None
            demo = finalize_match_demo(
                uow,
                match_id=match.id,
                source_path=source,
                map_name=match.map_name,
            )
            out_demo = demo.to_public_dict()

    if result.applied or result.reason in {"out_of_order", "server_mismatch"}:
        uow.matches.save(match)
    if result.applied:
        _enqueue_outbox(uow, match, result, correlation_id=correlation_id)
        # armed_pause already notified via maybe_arm_pause_on_round_start
        if review_pause_synced:
            notify_review_status(uow, match, JUDGE_REVIEW_TECH_PAUSE)
        elif armed_pause is None and _should_rebuild_overlay(result):
            rebuild_overlay_snapshot(
                uow,
                match,
                correlation_id=correlation_id,
                notify=True,
            )
        elif armed_pause is None and (
            event_type in {"tech_pause_started", "tech_pause_ended"}
        ):
            # Pause flag changed without match status transition — still refresh banner
            rebuild_overlay_snapshot(
                uow,
                match,
                correlation_id=correlation_id,
                notify=True,
            )

    out: dict[str, Any] = {
        "status": "ok" if result.applied else "rejected",
        "event_id": event_id,
        "match_id": match_id,
        "applied": result.applied,
        "reason": result.reason,
        "reconcile_needed": match.reconcile_needed,
        "transitions": list(result.transitions),
        "match": match.to_public_dict(),
    }
    if armed_pause is not None:
        out["armed_pause"] = {
            "confirmed": armed_pause.get("confirmed"),
            "command_id": armed_pause.get("command_id"),
            "status": armed_pause.get("status"),
        }
    if out_demo is not None:
        out["demo"] = out_demo
    return out


def _touch_server_heartbeat(
    uow: UnitOfWork,
    match,
    payload: dict[str, Any],
) -> None:
    sid = match.game_server_id
    if not sid:
        return
    server = uow.game_servers.get(sid)
    if server is None:
        return
    server.last_heartbeat = datetime.now(UTC)
    bv = payload.get("bridge_version")
    pv = payload.get("protocol_version")
    if isinstance(bv, str):
        server.bridge_version = bv
    if isinstance(pv, str):
        server.protocol_version = pv
    uow.game_servers.save(server)


def _should_rebuild_overlay(result) -> bool:
    """Bump overlay when score/status (or pause) visible on broadcast changes."""
    interesting = {"score_updated", "status_changed"}
    return bool(interesting.intersection(result.transitions))


def _enqueue_outbox(uow: UnitOfWork, match, result, *, correlation_id: str | None) -> None:
    if "status_changed" in result.transitions:
        uow.outbox.add(
            OutboxMessage(
                id=str(uuid4()),
                event_type=MATCH_STATUS_CHANGED,
                aggregate_type="match",
                aggregate_id=match.id,
                payload={
                    "match_id": match.id,
                    "from_status": result.previous_status,
                    "to_status": match.status,
                    "score": {
                        "team_a": match.score_team_a,
                        "team_b": match.score_team_b,
                    },
                },
                correlation_id=correlation_id,
            )
        )
    if "score_updated" in result.transitions:
        uow.outbox.add(
            OutboxMessage(
                id=str(uuid4()),
                event_type=MATCH_SCORE_UPDATED,
                aggregate_type="match",
                aggregate_id=match.id,
                payload={
                    "match_id": match.id,
                    "score": {
                        "team_a": match.score_team_a,
                        "team_b": match.score_team_b,
                    },
                    "round": match.round_number,
                },
                correlation_id=correlation_id,
            )
        )
    if "reconcile_needed" in result.transitions:
        uow.outbox.add(
            OutboxMessage(
                id=str(uuid4()),
                event_type=MATCH_RECONCILE_NEEDED,
                aggregate_type="match",
                aggregate_id=match.id,
                payload={
                    "match_id": match.id,
                    "last_sequence": match.last_sequence,
                },
                correlation_id=correlation_id,
            )
        )
