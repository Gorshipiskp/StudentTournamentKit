"""Protocol 2: WHIP publish / WHEP play credentials + MediaMTX authHTTP callback."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.domain.identity.caps import CAP_COMMENTATOR_WATCH
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.whep_sessions import whep_sessions
from app.infrastructure.security.mediamtx_credentials import (
    issue_mediamtx_bearer,
    parse_mediamtx_bearer,
    public_credential_response,
)
from app.infrastructure.security.session_token import parse_session_token
from app.presentation.http.deps.organizer_auth import RequireOrganizer

logger = logging.getLogger("stk.whip")

router = APIRouter(tags=["whip"])


def _require_match(match_id: str) -> None:
    with SqlAlchemyUnitOfWork() as uow:
        if uow.matches.get(match_id) is None:
            raise HTTPException(status_code=404, detail=f"match not found: {match_id}")


def _authorize_commentator(match_id: str, authorization: str | None):
    if not authorization:
        raise HTTPException(status_code=401, detail="commentator session required")
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
    return session


@router.post("/api/v1/matches/{match_id}/whip-publish")
def post_whip_publish(
    match_id: str,
    _organizer: RequireOrganizer,
) -> dict[str, Any]:
    _require_match(match_id)
    try:
        issued = issue_mediamtx_bearer(match_id=match_id, action="publish")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    logger.info("whip_publish issued match_id=%s path=%s ttl=%s", match_id, issued["path"], issued["ttl"])
    return public_credential_response(issued)


@router.post("/api/v1/matches/{match_id}/whep-play")
def post_whep_play(
    match_id: str,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    session = _authorize_commentator(match_id, authorization)
    _require_match(match_id)
    try:
        issued = issue_mediamtx_bearer(match_id=match_id, action="read")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    claims = parse_mediamtx_bearer(issued["bearer"])
    ok = whep_sessions.try_acquire(
        match_id,
        jti=claims["jti"],
        expires_at=float(claims["exp"]),
        invite_id=session.invite_id,
    )
    if not ok:
        raise HTTPException(
            status_code=429,
            detail="whep limit reached (max 2 concurrent credentials per match)",
        )
    logger.info(
        "whep_play issued match_id=%s path=%s ttl=%s active=%s invite=%s",
        match_id,
        issued["path"],
        issued["ttl"],
        whep_sessions.active_count(match_id),
        session.invite_id[:8],
    )
    return public_credential_response(issued)


class MediaMtxAuthBody(BaseModel):
    """MediaMTX authMethod: http callback payload (subset)."""

    user: str = ""
    password: str = ""
    action: str = Field(description="publish|read|playback|api|…")
    path: str = ""
    protocol: str = ""
    ip: str = ""
    id: str = ""
    query: str = ""


@router.post("/api/v1/internal/mediamtx-auth")
def post_mediamtx_auth(body: MediaMtxAuthBody) -> dict[str, str]:
    """
    MediaMTX HTTP auth: 2xx accept, else deny.
    Bearer is passed as Authorization on WHIP/WHEP → usually `password` here.
    """
    token = (body.password or body.user or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing token")
    try:
        claims = parse_mediamtx_bearer(token)
    except ValueError:
        # Do not echo token
        raise HTTPException(status_code=401, detail="unauthorized") from None

    action = body.action.strip().lower()
    if action == "publish" and claims["act"] != "publish":
        raise HTTPException(status_code=403, detail="publish requires publish bearer")
    if action in ("read", "playback") and claims["act"] != "read":
        raise HTTPException(status_code=403, detail="read requires read bearer")
    if action in ("api", "metrics", "pprof"):
        raise HTTPException(status_code=403, detail="api not allowed via stream bearer")

    req_path = (body.path or "").lstrip("/")
    if req_path and req_path != claims["path"]:
        raise HTTPException(status_code=403, detail="path mismatch")

    logger.info(
        "mediamtx_auth ok action=%s path=%s jti=%s",
        action,
        claims["path"],
        claims["jti"],
    )
    return {"status": "ok"}
