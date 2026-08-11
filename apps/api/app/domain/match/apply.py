"""Apply normalized game events to Match (idempotent domain handler)."""

from __future__ import annotations

from typing import Any

from app.domain.match.entities import (
    MATCH_CANCELLED,
    MATCH_COMPLETED,
    MATCH_FORFEITED,
    MATCH_KNIFE,
    MATCH_LIVE,
    MATCH_SCHEDULED,
    MATCH_SERVER_ASSIGNED,
    MATCH_WARMUP,
    ApplyResult,
    Match,
)

_KNOWN_TYPES = frozenset(
    {
        "match_loaded",
        "round_start",
        "round_end",
        "score_changed",
        "tech_pause_started",
        "tech_pause_ended",
        "match_completed",
        "heartbeat",
    }
)

_PRE_LIVE = frozenset(
    {
        MATCH_SCHEDULED,
        MATCH_SERVER_ASSIGNED,
        MATCH_WARMUP,
        MATCH_KNIFE,
    }
)

_TERMINAL = frozenset({MATCH_COMPLETED, MATCH_FORFEITED, MATCH_CANCELLED})


def apply_game_event(
    match: Match,
    *,
    event_type: str,
    sequence: int,
    payload: dict[str, Any] | None = None,
    server_id: str | None = None,
) -> ApplyResult:
    """Mutate match from one normalized event.

    Sequence rules (INVARIANTS §6):
    - expected next = last_sequence + 1 (first event: sequence >= 1)
    - gap / OOO → reconcile_needed; OOO does not overwrite score/history
    """
    payload = payload or {}
    if event_type not in _KNOWN_TYPES:
        return ApplyResult(applied=False, reason="unknown_type")

    if server_id and match.game_server_id and server_id != match.game_server_id:
        return ApplyResult(applied=False, reason="server_mismatch")

    expected = match.last_sequence + 1
    if match.last_sequence == 0:
        if sequence < 1:
            return ApplyResult(applied=False, reason="invalid_sequence")
        if sequence > 1:
            match.reconcile_needed = True
    elif sequence < expected:
        match.reconcile_needed = True
        return ApplyResult(applied=False, reason="out_of_order")
    elif sequence > expected:
        match.reconcile_needed = True

    previous_status = match.status
    score_changed = False
    transitions: list[str] = []
    had_gap = match.last_sequence > 0 and sequence > expected

    if event_type == "match_loaded":
        map_name = payload.get("map")
        if isinstance(map_name, str) and map_name:
            match.map_name = map_name
        if match.status in {MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED}:
            match.status = MATCH_WARMUP
        match.phase = "warmup"

    elif event_type == "round_start":
        round_no = payload.get("round")
        if isinstance(round_no, int) and round_no >= 0:
            match.round_number = round_no
        phase = payload.get("phase")
        if isinstance(phase, str) and phase:
            match.phase = phase
        if match.status in _PRE_LIVE:
            match.status = MATCH_LIVE

    elif event_type == "round_end":
        score_changed = _apply_score(match, payload)
        round_no = payload.get("round")
        if isinstance(round_no, int) and round_no >= 0:
            match.round_number = round_no
        map_name = payload.get("map")
        if isinstance(map_name, str) and map_name:
            match.map_name = map_name
        match.phase = "freeze"
        if match.status not in _TERMINAL and match.status != MATCH_LIVE:
            match.status = MATCH_LIVE

    elif event_type == "score_changed":
        score_changed = _apply_score(match, payload)
        round_no = payload.get("round")
        if isinstance(round_no, int) and round_no >= 0:
            match.round_number = round_no

    elif event_type == "tech_pause_started":
        match.actual_paused = True

    elif event_type == "tech_pause_ended":
        match.actual_paused = False

    elif event_type == "match_completed":
        if _apply_score(match, payload):
            score_changed = True
        reason = payload.get("reason", "normal")
        match.status = MATCH_FORFEITED if reason == "forfeit" else MATCH_COMPLETED
        match.phase = "ended"
        match.actual_paused = False

    elif event_type == "heartbeat":
        pass

    status_changed = previous_status != match.status
    if status_changed:
        transitions.append("status_changed")
    if score_changed:
        transitions.append("score_updated")
    if had_gap:
        transitions.append("reconcile_needed")

    if status_changed or score_changed:
        match.version += 1

    match.last_sequence = max(match.last_sequence, sequence)

    return ApplyResult(
        applied=True,
        reason="ok",
        status_changed=status_changed,
        score_changed=score_changed,
        previous_status=previous_status,
        transitions=tuple(dict.fromkeys(transitions)),
    )


def _apply_score(match: Match, payload: dict[str, Any]) -> bool:
    score = payload.get("score")
    if not isinstance(score, dict):
        return False
    a = score.get("team_a")
    b = score.get("team_b")
    if not isinstance(a, int) or not isinstance(b, int):
        return False
    if a == match.score_team_a and b == match.score_team_b:
        return False
    match.score_team_a = a
    match.score_team_b = b
    return True
