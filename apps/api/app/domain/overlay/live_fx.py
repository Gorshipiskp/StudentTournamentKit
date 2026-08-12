"""Build ephemeral overlay FX payloads from CS2 events."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Default bomb fuse (classic competitive); Bridge may override via payload.timer_sec
DEFAULT_BOMB_TIMER_SEC = 40

# round_start intentionally omitted: scoreboard already shows the round, and a
# quick round_start FX was wiping the round_win celebration.
FX_EVENT_TYPES = frozenset(
    {
        "bomb_planted",
        "bomb_defuse_start",
        "bomb_defused",
        "bomb_exploded",
        "round_end",
    }
)

_LABELS = {
    "bomb_planted": "Бомба заложена",
    "bomb_defuse_start": "Дефьюз",
    "bomb_defused": "Бомба разминирована",
    "bomb_exploded": "Взрыв",
    "round_end": "Победа в раунде",
}

_TTL_MS = {
    "bomb_planted": 45_000,  # covers fuse + buffer; client may clear earlier
    "bomb_defuse_start": 12_000,
    "bomb_defused": 5_000,
    "bomb_exploded": 5_000,
    "round_end": 7_500,
}


def build_live_fx(
    event_type: str,
    payload: dict[str, Any] | None,
    *,
    sequence: int,
    at: str | None = None,
) -> dict[str, Any] | None:
    """Return overlay `data.fx` object or None if event has no FX."""
    if event_type not in FX_EVENT_TYPES:
        return None
    payload = payload or {}
    kind = event_type
    if event_type == "round_end":
        kind = "round_win"
    elif event_type == "bomb_defuse_start":
        kind = "bomb_defusing"

    fx: dict[str, Any] = {
        "kind": kind,
        "at": at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "ttl_ms": int(_TTL_MS.get(event_type, 4_000)),
        "seq": int(sequence),
        "label": _LABELS.get(event_type, event_type),
    }

    site = payload.get("site")
    if isinstance(site, (int, str)) and str(site):
        fx["site"] = site

    side = payload.get("side") or payload.get("winner_side")
    if side in {"team_a", "team_b", "ct", "t"}:
        if side == "ct":
            side = "team_a"
        elif side == "t":
            side = "team_b"
        fx["side"] = side

    if event_type == "round_end":
        winner = payload.get("winner")
        if winner in {"team_a", "team_b", "ct", "t"}:
            fx["side"] = {"ct": "team_a", "t": "team_b"}.get(str(winner), winner)
        reason = payload.get("reason") or payload.get("win_reason")
        if isinstance(reason, str) and reason:
            fx["reason"] = reason
        round_no = payload.get("round")
        if isinstance(round_no, int) and round_no > 0:
            fx["round"] = round_no
        if fx.get("side") == "team_a":
            fx["label"] = "Победа CT"
        elif fx.get("side") == "team_b":
            fx["label"] = "Победа T"

    if event_type == "bomb_planted":
        timer = payload.get("timer_sec", DEFAULT_BOMB_TIMER_SEC)
        try:
            fx["timer_sec"] = max(1, int(timer))
        except (TypeError, ValueError):
            fx["timer_sec"] = DEFAULT_BOMB_TIMER_SEC

    if event_type == "bomb_defuse_start":
        fx["has_kit"] = bool(payload.get("has_kit"))

    return fx
