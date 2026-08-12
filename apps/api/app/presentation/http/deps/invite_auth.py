"""HTTP deps: Bearer invite-session + capability checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Path

from app.domain.identity.entities import InviteSession
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.session_token import parse_session_token


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="missing Authorization bearer")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise HTTPException(status_code=401, detail="invalid Authorization bearer")
    return value.strip()


def get_invite_session(
    authorization: Annotated[str | None, Header()] = None,
) -> InviteSession:
    raw = _extract_bearer(authorization)
    try:
        session = parse_session_token(raw)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    # Live revoke check: if invite revoked after redeem, reject.
    with SqlAlchemyUnitOfWork() as uow:
        invite = uow.invites.get(session.invite_id)
    if invite is None or invite.is_revoked():
        raise HTTPException(status_code=401, detail="invite revoked")
    return session


def require_match_caps(*needed: str) -> Callable[..., InviteSession]:
    """Require Bearer session scoped to path match_id with all capabilities."""

    def _dep(
        match_id: Annotated[str, Path()],
        session: Annotated[InviteSession, Depends(get_invite_session)],
    ) -> InviteSession:
        if not session.requires_match(match_id):
            raise HTTPException(status_code=403, detail="session not scoped to this match")
        missing = [c for c in needed if not session.has_cap(c)]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"missing capabilities: {', '.join(missing)}",
            )
        return session

    return _dep
