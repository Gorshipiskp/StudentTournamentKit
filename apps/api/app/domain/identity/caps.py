"""Capability strings for invite-scoped sessions (F4)."""

from __future__ import annotations

ROLE_JUDGE = "judge"
ROLE_COMMENTATOR = "commentator"

CAP_JUDGE_REVIEW = "judge.review"
CAP_JUDGE_RESOLVE = "judge.resolve"
CAP_COMMENTATOR_WATCH = "commentator.watch"
CAP_OVERLAY_READ = "overlay.read"

ROLE_CAPS: dict[str, frozenset[str]] = {
    ROLE_JUDGE: frozenset({CAP_JUDGE_REVIEW, CAP_JUDGE_RESOLVE}),
    ROLE_COMMENTATOR: frozenset({CAP_COMMENTATOR_WATCH, CAP_OVERLAY_READ}),
}

ALLOWED_ROLES = frozenset(ROLE_CAPS)


def caps_for_role(role: str) -> frozenset[str]:
    try:
        return ROLE_CAPS[role]
    except KeyError as exc:
        raise ValueError(f"unknown invite role: {role}") from exc
