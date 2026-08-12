"""Organizer auth — instance bootstrap login."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.infrastructure.security.organizer_token import (
    issue_organizer_token,
    verify_organizer_credentials,
)
from app.presentation.http.deps.organizer_auth import RequireOrganizer

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(default="organizer")
    password: str


@router.post("/login")
def post_login(body: LoginBody) -> dict[str, Any]:
    if not verify_organizer_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    token, session = issue_organizer_token()
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": session.role,
        "expires_at": session.expires_at.isoformat(),
    }


@router.post("/logout")
def post_logout(_session: RequireOrganizer) -> dict[str, bool]:
    # Stateless token — client discards bearer; endpoint confirms session was valid.
    return {"ok": True}


@router.post("/refresh")
def post_refresh(_session: RequireOrganizer) -> dict[str, Any]:
    token, session = issue_organizer_token()
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": session.role,
        "expires_at": session.expires_at.isoformat(),
    }


@router.get("/me")
def get_me(session: RequireOrganizer) -> dict[str, Any]:
    return {
        "role": session.role,
        "expires_at": session.expires_at.isoformat(),
    }
