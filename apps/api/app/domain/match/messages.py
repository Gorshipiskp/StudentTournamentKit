"""Match status fanout for judge / commentator UI (People Slice)."""

from __future__ import annotations

PROTOCOL_VERSION = 1
TYPE_MATCH_STATUS = "match.status"

# Outbox event types that trigger judge hub push
JUDGE_REVIEW_REQUESTED = "judge.review_requested"
JUDGE_REVIEW_CANCELLED = "judge.review_cancelled"
JUDGE_REVIEW_RESOLVED = "judge.review_resolved"
JUDGE_REVIEW_TECH_PAUSE = "judge.review_tech_pause"

JUDGE_NOTIFY_EVENTS = frozenset(
    {
        JUDGE_REVIEW_REQUESTED,
        JUDGE_REVIEW_CANCELLED,
        JUDGE_REVIEW_RESOLVED,
        JUDGE_REVIEW_TECH_PAUSE,
    }
)
