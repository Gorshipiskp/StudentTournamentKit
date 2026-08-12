"""Organizer: force score/round onto match + overlay (from CS2 or manual)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.issue_match_command import issue_match_command
from app.application.commands.rebuild_overlay import (
    rebuild_overlay_snapshot,
    seed_overlay_and_production,
)
from app.application.commands.write_audit import write_audit
from app.application.unit_of_work import UnitOfWork
from app.domain.audit.entities import ACTION_ORGANIZER_SCORE_SYNC, ACTOR_ORGANIZER
from app.domain.match.game_command import TYPE_SNAPSHOT
from app.domain.match.reconcile import apply_snapshot_to_match
from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.adapters.cs2.command_client import GameCommandTransport


def sync_match_scoreboard(
    uow: UnitOfWork,
    *,
    match_id: str,
    from_server: bool = False,
    score_team_a: int | None = None,
    score_team_b: int | None = None,
    round_number: int | None = None,
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
) -> dict[str, Any]:
    """
    Push scoreboard to broadcast.

    from_server=True: GetSnapshot from CS2 Bridge → repair match → overlay.
    from_server=False: write provided score/round into match → overlay.
    Always clears conflicting manual overlay overrides.
    """
    if from_server:
        return _sync_from_server(
            uow,
            match_id=match_id,
            correlation_id=correlation_id,
            transport=transport,
        )
    return _sync_manual(
        uow,
        match_id=match_id,
        score_team_a=score_team_a,
        score_team_b=score_team_b,
        round_number=round_number,
        correlation_id=correlation_id,
    )


def _sync_from_server(
    uow: UnitOfWork,
    *,
    match_id: str,
    correlation_id: str | None,
    transport: GameCommandTransport | None,
) -> dict[str, Any]:
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    if not match.game_server_id:
        raise ValueError("матч без игрового сервера — нечего запрашивать")

    before = match.to_public_dict()
    command_result = issue_match_command(
        uow,
        match_id=match_id,
        command_type=TYPE_SNAPSHOT,
        command_id=str(uuid4()),
        correlation_id=correlation_id,
        transport=transport,
        commit=False,
    )
    if not command_result.get("confirmed"):
        raise ValueError(
            command_result.get("error")
            or "сервер не ответил на запрос снимка (GetSnapshot)"
        )
    result = command_result.get("ack_result") or {}
    snap = result.get("snapshot") if isinstance(result, dict) else None
    if not isinstance(snap, dict):
        raise ValueError("в ответе сервера нет snapshot")

    match = uow.matches.get(match_id)
    assert match is not None
    changed = apply_snapshot_to_match(match, snap)
    uow.matches.save(match)
    cleared = _clear_score_overrides(uow, match_id)

    if changed:
        uow.outbox.add(
            OutboxMessage(
                id=str(uuid4()),
                event_type="match.reconciled",
                aggregate_type="match",
                aggregate_id=match.id,
                payload={
                    "match_id": match.id,
                    "changed": changed,
                    "last_sequence": match.last_sequence,
                    "source": "organizer.score_sync",
                },
                correlation_id=correlation_id,
            )
        )

    after = match.to_public_dict()
    write_audit(
        uow,
        match_id=match_id,
        action=ACTION_ORGANIZER_SCORE_SYNC,
        actor_type=ACTOR_ORGANIZER,
        tournament_id=match.tournament_id,
        payload={
            "source": "server",
            "before": {
                "score": before["score"],
                "round": before["round"],
                "phase": before.get("phase"),
            },
            "after": {
                "score": after["score"],
                "round": after["round"],
                "phase": after.get("phase"),
            },
            "changed": changed,
            "cleared_overrides": cleared,
        },
        correlation_id=correlation_id,
    )
    message = rebuild_overlay_snapshot(
        uow, match, correlation_id=correlation_id, notify=True
    )
    return {
        "ok": True,
        "source": "server",
        "match": after,
        "overlay": message,
        "snapshot": snap,
        "changed": changed,
        "note": (
            f"С сервера: {after['score']['team_a']}:{after['score']['team_b']}, "
            f"раунд {after['round']}, фаза {after.get('phase') or '—'}"
        ),
    }


def _sync_manual(
    uow: UnitOfWork,
    *,
    match_id: str,
    score_team_a: int | None,
    score_team_b: int | None,
    round_number: int | None,
    correlation_id: str | None,
) -> dict[str, Any]:
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")

    for label, value in (
        ("score_team_a", score_team_a),
        ("score_team_b", score_team_b),
        ("round", round_number),
    ):
        if value is not None and value < 0:
            raise ValueError(f"{label} must be >= 0")

    before = {
        "score_team_a": match.score_team_a,
        "score_team_b": match.score_team_b,
        "round": match.round_number,
    }

    if score_team_a is not None:
        match.score_team_a = int(score_team_a)
    if score_team_b is not None:
        match.score_team_b = int(score_team_b)
    if round_number is not None:
        match.round_number = int(round_number)

    uow.matches.save(match)
    cleared = _clear_score_overrides(uow, match_id)

    after = {
        "score_team_a": match.score_team_a,
        "score_team_b": match.score_team_b,
        "round": match.round_number,
    }
    write_audit(
        uow,
        match_id=match_id,
        action=ACTION_ORGANIZER_SCORE_SYNC,
        actor_type=ACTOR_ORGANIZER,
        tournament_id=match.tournament_id,
        payload={
            "source": "manual",
            "before": before,
            "after": after,
            "cleared_overrides": cleared,
        },
        correlation_id=correlation_id,
    )
    message = rebuild_overlay_snapshot(
        uow, match, correlation_id=correlation_id, notify=True
    )
    return {
        "ok": True,
        "source": "manual",
        "match": match.to_public_dict(),
        "overlay": message,
        "note": "Табло записано вручную и обновлено на эфире",
    }


def _clear_score_overrides(uow: UnitOfWork, match_id: str) -> list[str]:
    overlay = uow.overlays.get(match_id)
    if overlay is None:
        match = uow.matches.get(match_id)
        if match is None:
            return []
        seed_overlay_and_production(uow, match)
        overlay = uow.overlays.get(match_id)
    if overlay is None:
        return []
    overrides = dict(overlay.manual_overrides)
    cleared = [k for k in ("score_team_a", "score_team_b", "round") if k in overrides]
    if not cleared:
        return []
    for key in cleared:
        overrides.pop(key, None)
    overlay.manual_overrides = overrides
    uow.overlays.save(overlay)
    return cleared
