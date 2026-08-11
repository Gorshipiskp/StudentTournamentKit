"""ReviewStatus dimension — separate from MatchStatus (ADR-026, F3)."""

from __future__ import annotations

REVIEW_NONE = "none"
REVIEW_REQUESTED = "requested"
REVIEW_PAUSE_PENDING = "pause_pending"
REVIEW_PAUSED = "paused"
REVIEW_RESOLVED = "resolved"
REVIEW_CANCELLED = "cancelled"

RESOLUTION_CONTINUE = "continue"
RESOLUTION_FORFEIT = "forfeit"

_ACTIVE = frozenset(
    {REVIEW_REQUESTED, REVIEW_PAUSE_PENDING, REVIEW_PAUSED}
)
