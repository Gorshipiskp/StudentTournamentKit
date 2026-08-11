"""Apply game snapshot onto Match — recovery path (INVARIANTS §6/§9)."""

from __future__ import annotations

from typing import Any

from app.domain.match.entities import (
    MATCH_COMPLETED,
    MATCH_FORFEITED,
    MATCH_LIVE,
    Match,
)


def apply_snapshot_to_match(match: Match, snapshot: dict[str, Any]) -> list[str]:
    """Repair platform view from authoritative game snapshot. Returns changed fields."""
    changed: list[str] = []

    score = snapshot.get("score")
    if isinstance(score, dict):
        a, b = score.get("team_a"), score.get("team_b")
        if isinstance(a, int) and isinstance(b, int):
            if match.score_team_a != a or match.score_team_b != b:
                match.score_team_a = a
                match.score_team_b = b
                changed.append("score")
    elif isinstance(score, list) and len(score) >= 2:
        a, b = score[0], score[1]
        if isinstance(a, int) and isinstance(b, int):
            if match.score_team_a != a or match.score_team_b != b:
                match.score_team_a = a
                match.score_team_b = b
                changed.append("score")

    round_no = snapshot.get("round")
    if isinstance(round_no, int) and round_no != match.round_number:
        match.round_number = round_no
        changed.append("round")

    phase = snapshot.get("phase")
    if isinstance(phase, str) and phase and phase != match.phase:
        match.phase = phase
        changed.append("phase")

    map_name = snapshot.get("map")
    if isinstance(map_name, str) and map_name and map_name != match.map_name:
        match.map_name = map_name
        changed.append("map")

    paused = snapshot.get("paused")
    if isinstance(paused, bool) and paused != match.actual_paused:
        match.actual_paused = paused
        changed.append("actual_paused")

    last_seq = snapshot.get("last_sequence")
    if isinstance(last_seq, int) and last_seq > match.last_sequence:
        match.last_sequence = last_seq
        changed.append("last_sequence")

    completed = snapshot.get("completed")
    if completed is True and match.status not in {MATCH_COMPLETED, MATCH_FORFEITED}:
        match.status = MATCH_COMPLETED
        match.phase = "ended"
        changed.append("status")
    elif (
        completed is False
        and match.status not in {MATCH_COMPLETED, MATCH_FORFEITED, "cancelled"}
        and match.status != MATCH_LIVE
        and (match.round_number > 0 or match.score_team_a + match.score_team_b > 0)
    ):
        match.status = MATCH_LIVE
        changed.append("status")

    if match.reconcile_needed:
        match.reconcile_needed = False
        changed.append("reconcile_needed_cleared")

    if changed:
        match.version += 1

    return changed
