"""Reconcile match from GetSnapshot (recovery after gap / drift)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.issue_match_command import issue_match_command
from app.application.unit_of_work import UnitOfWork
from app.domain.match.game_command import TYPE_SNAPSHOT
from app.domain.match.reconcile import apply_snapshot_to_match
from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.adapters.cs2.command_client import GameCommandTransport


def reconcile_match_from_snapshot(
    uow: UnitOfWork,
    *,
    match_id: str,
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch GetSnapshot (or use provided snapshot) and repair match view."""
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError("match not found")

    command_result: dict[str, Any] | None = None
    snap = snapshot
    if snap is None:
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
            uow.commit()
            return {
                "ok": False,
                "reason": "snapshot_command_failed",
                "command": command_result,
                "match": match.to_public_dict(),
                "changed": [],
            }
        result = command_result.get("ack_result") or {}
        snap = result.get("snapshot") if isinstance(result, dict) else None
        if not isinstance(snap, dict):
            uow.commit()
            return {
                "ok": False,
                "reason": "missing_snapshot_in_ack",
                "command": command_result,
                "match": match.to_public_dict(),
                "changed": [],
            }

    match = uow.matches.get(match_id)
    assert match is not None
    before = match.to_public_dict()
    changed = apply_snapshot_to_match(match, snap)
    uow.matches.save(match)
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
                },
                correlation_id=correlation_id,
            )
        )
    uow.commit()
    return {
        "ok": True,
        "changed": changed,
        "before": {
            "score": before["score"],
            "round": before["round"],
            "actual_paused": before["actual_paused"],
            "last_sequence": before["last_sequence"],
            "reconcile_needed": before["reconcile_needed"],
        },
        "match": match.to_public_dict(),
        "snapshot": snap,
        "command": command_result,
    }
