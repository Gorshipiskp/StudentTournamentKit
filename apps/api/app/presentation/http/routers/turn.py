"""TURN ephemeral credentials API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException

from app.domain.identity.caps import CAP_COMMENTATOR_WATCH
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.agent_auth import verify_agent_token
from app.infrastructure.security.session_token import parse_session_token
from app.infrastructure.security.turn_credentials import issue_turn_credentials

router = APIRouter(prefix="/api/v1/matches", tags=["turn"])


def _authorize_turn(
    match_id: str,
    *,
    authorization: str | None,
    agent_header: str | None,
) -> None:
    if verify_agent_token(agent_header):
        return
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="agent token or commentator session required",
        )
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise HTTPException(status_code=401, detail="invalid Authorization bearer")
    try:
        session = parse_session_token(value.strip())
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if not session.requires_match(match_id):
        raise HTTPException(status_code=403, detail="session not scoped to this match")
    if not session.has_cap(CAP_COMMENTATOR_WATCH):
        raise HTTPException(status_code=403, detail="missing commentator.watch")
    with SqlAlchemyUnitOfWork() as uow:
        invite = uow.invites.get(session.invite_id)
        if invite is None or invite.is_revoked():
            raise HTTPException(status_code=401, detail="invite revoked")


@router.post("/{match_id}/turn-credentials")
def post_turn_credentials(
    match_id: str,
    authorization: Annotated[str | None, Header()] = None,
    x_stk_agent_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _authorize_turn(
        match_id,
        authorization=authorization,
        agent_header=x_stk_agent_token,
    )
    with SqlAlchemyUnitOfWork() as uow:
        if uow.matches.get(match_id) is None:
            raise HTTPException(status_code=404, detail=f"match not found: {match_id}")
    try:
        return issue_turn_credentials(match_id=match_id)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
