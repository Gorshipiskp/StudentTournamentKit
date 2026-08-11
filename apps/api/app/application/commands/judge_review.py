"""Judge review workflow — request / cancel / resolve (no UI)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.issue_match_command import issue_match_command
from app.application.unit_of_work import UnitOfWork
from app.domain.match.entities import (
    MATCH_CANCELLED,
    MATCH_COMPLETED,
    MATCH_FORFEITED,
    MATCH_KNIFE,
    MATCH_LIVE,
    MATCH_SERVER_ASSIGNED,
    MATCH_WARMUP,
    Match,
)
from app.domain.match.game_command import TYPE_FORFEIT, TYPE_PAUSE, TYPE_RESUME
from app.domain.match.review import (
    RESOLUTION_CONTINUE,
    RESOLUTION_FORFEIT,
    REVIEW_CANCELLED,
    REVIEW_NONE,
    REVIEW_PAUSE_PENDING,
    REVIEW_PAUSED,
    REVIEW_REQUESTED,
    REVIEW_RESOLVED,
)
from app.domain.shared.outbox import OutboxMessage
from app.infrastructure.adapters.cs2.command_client import GameCommandTransport

_TERMINAL_MATCH = frozenset({MATCH_COMPLETED, MATCH_FORFEITED, MATCH_CANCELLED})
_REVIEWABLE_MATCH = frozenset(
    {MATCH_LIVE, MATCH_WARMUP, MATCH_KNIFE, MATCH_SERVER_ASSIGNED}
)


class JudgeConflict(Exception):
    """409-style domain conflict."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def request_review(uow: UnitOfWork, *, match_id: str) -> Match:
    match = _require_match(uow, match_id)
    if match.status in _TERMINAL_MATCH:
        raise JudgeConflict("match already finished")
    if match.status not in _REVIEWABLE_MATCH:
        raise JudgeConflict(f"cannot request review in status={match.status}")
    if match.review_status in {
        REVIEW_REQUESTED,
        REVIEW_PAUSE_PENDING,
        REVIEW_PAUSED,
    }:
        raise JudgeConflict(f"review already active: {match.review_status}")
    if match.review_status not in {REVIEW_NONE, REVIEW_CANCELLED, REVIEW_RESOLVED}:
        raise JudgeConflict(f"invalid review_status={match.review_status}")

    match.review_status = REVIEW_REQUESTED
    match.review_resolution = None
    match.version += 1
    uow.matches.save(match)
    _outbox_review(uow, match, "judge.review_requested")
    uow.commit()
    return match


def cancel_review(uow: UnitOfWork, *, match_id: str) -> Match:
    match = _require_match(uow, match_id)
    if match.review_status != REVIEW_REQUESTED:
        raise JudgeConflict(
            "cancel only allowed while review_status=requested (before pause)"
        )
    match.review_status = REVIEW_CANCELLED
    match.version += 1
    uow.matches.save(match)
    _outbox_review(uow, match, "judge.review_cancelled")
    uow.commit()
    return match


def resolve_review(
    uow: UnitOfWork,
    *,
    match_id: str,
    action: str,
    expected_version: int,
    losing_team: str | None = None,
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
) -> dict[str, Any]:
    match = _require_match(uow, match_id)
    if match.status in _TERMINAL_MATCH:
        raise JudgeConflict("stale resolve: match already finished")
    if match.version != expected_version:
        raise JudgeConflict(
            f"version conflict: expected {expected_version}, got {match.version}"
        )
    if match.review_status != REVIEW_PAUSED:
        raise JudgeConflict(
            f"resolve requires review_status=paused, got {match.review_status}"
        )
    if action not in {RESOLUTION_CONTINUE, RESOLUTION_FORFEIT}:
        raise ValueError("action must be continue or forfeit")

    if action == RESOLUTION_CONTINUE:
        command_result = issue_match_command(
            uow,
            match_id=match_id,
            command_type=TYPE_RESUME,
            command_id=str(uuid4()),
            correlation_id=correlation_id,
            transport=transport,
            commit=False,
        )
        match = _require_match(uow, match_id)
        match.review_status = REVIEW_RESOLVED
        match.review_resolution = RESOLUTION_CONTINUE
        match.version += 1
        uow.matches.save(match)
        _outbox_review(uow, match, "judge.review_resolved")
        uow.commit()
    else:
        if losing_team not in {"team_a", "team_b"}:
            raise ValueError("losing_team must be team_a or team_b")
        command_result = issue_match_command(
            uow,
            match_id=match_id,
            command_type=TYPE_FORFEIT,
            payload={"losing_team": losing_team},
            command_id=str(uuid4()),
            correlation_id=correlation_id,
            transport=transport,
            commit=False,
        )
        match = _require_match(uow, match_id)
        match.review_status = REVIEW_RESOLVED
        match.review_resolution = RESOLUTION_FORFEIT
        match.version += 1
        uow.matches.save(match)
        _outbox_review(uow, match, "judge.review_resolved")
        uow.commit()

    return {
        "match": match.to_public_dict(),
        "action": action,
        "command": command_result,
    }


def maybe_arm_pause_on_round_start(
    uow: UnitOfWork,
    match: Match,
    *,
    phase: str | None,
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
) -> dict[str, Any] | None:
    """If review requested and buy phase — PauseMatch → pause_pending/paused."""
    if match.review_status != REVIEW_REQUESTED:
        return None
    # VISION: pause at start of next round buy
    if phase is not None and phase != "buy":
        return None

    match.review_status = REVIEW_PAUSE_PENDING
    match.version += 1
    uow.matches.save(match)

    cmd = issue_match_command(
        uow,
        match_id=match.id,
        command_type=TYPE_PAUSE,
        payload={"reason": "judge_review"},
        command_id=str(uuid4()),
        correlation_id=correlation_id,
        transport=transport,
        commit=False,
    )
    match = _require_match(uow, match.id)
    if cmd.get("confirmed"):
        match.review_status = REVIEW_PAUSED
        if match.status not in _TERMINAL_MATCH:
            match.status = MATCH_LIVE
        uow.matches.save(match)
    return cmd


def mark_review_paused_if_pending(match: Match) -> bool:
    """When actual tech pause observed (event) while pause_pending."""
    if match.review_status == REVIEW_PAUSE_PENDING and match.actual_paused:
        match.review_status = REVIEW_PAUSED
        if match.status not in _TERMINAL_MATCH:
            match.status = MATCH_LIVE
        return True
    return False


def _require_match(uow: UnitOfWork, match_id: str) -> Match:
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError("match not found")
    return match


def _outbox_review(uow: UnitOfWork, match: Match, event_type: str) -> None:
    uow.outbox.add(
        OutboxMessage(
            id=str(uuid4()),
            event_type=event_type,
            aggregate_type="match",
            aggregate_id=match.id,
            payload={
                "match_id": match.id,
                "review_status": match.review_status,
                "review_resolution": match.review_resolution,
                "match_status": match.status,
                "version": match.version,
            },
        )
    )
