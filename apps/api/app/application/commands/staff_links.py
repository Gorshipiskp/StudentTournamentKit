"""Create judge + commentator invites and public deep-link paths."""

from __future__ import annotations

import os
from typing import Any

from app.application.commands.invite_tokens import create_invite
from app.application.unit_of_work import UnitOfWork
from app.domain.identity.caps import ROLE_COMMENTATOR, ROLE_JUDGE


def _origin(name: str, default: str) -> str:
    return (os.environ.get(name) or default).rstrip("/")


def create_match_staff_links(
    uow: UnitOfWork,
    *,
    match_id: str,
) -> dict[str, Any]:
    """Issue judge + commentator invites; return copy-paste URLs for admin UI."""
    if uow.matches.get(match_id) is None:
        raise KeyError(f"match not found: {match_id}")

    # create_invite commits each call — fine for admin pack
    judge = create_invite(uow, match_id=match_id, role=ROLE_JUDGE)
    commentator = create_invite(uow, match_id=match_id, role=ROLE_COMMENTATOR)

    dash = _origin("STK_DASHBOARD_ORIGIN", "http://127.0.0.1:5174")
    judge_origin = _origin("STK_JUDGE_ORIGIN", "http://127.0.0.1:5175")
    watch_origin = _origin("STK_WATCH_ORIGIN", "http://127.0.0.1:5173")

    director_url = f"{dash}/director/{match_id}"
    judge_url = f"{judge_origin}/?token={judge.raw_token}"
    watch_url = f"{watch_origin}/watch?token={commentator.raw_token}"

    return {
        "match_id": match_id,
        "director_url": director_url,
        "judge": {
            **judge.to_public_dict(),
            "url": judge_url,
        },
        "commentator": {
            **commentator.to_public_dict(),
            "url": watch_url,
        },
        "origins": {
            "dashboard": dash,
            "judge": judge_origin,
            "watch": watch_origin,
        },
    }
