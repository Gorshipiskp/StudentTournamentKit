"""HTTP deps: Bearer organizer session."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.domain.identity.organizer import OrganizerSession
from app.infrastructure.security.organizer_token import parse_organizer_token


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="missing Authorization bearer")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise HTTPException(status_code=401, detail="invalid Authorization bearer")
    return value.strip()


def get_organizer_session(
    authorization: Annotated[str | None, Header()] = None,
) -> OrganizerSession:
    raw = _extract_bearer(authorization)
    try:
        session = parse_organizer_token(raw)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if not session.is_organizer():
        raise HTTPException(status_code=401, detail="not an organizer session")
    return session


RequireOrganizer = Annotated[OrganizerSession, Depends(get_organizer_session)]
