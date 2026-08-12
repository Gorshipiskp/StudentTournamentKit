"""Invite create / redeem / revoke API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.commands.invite_tokens import (
    InviteError,
    create_invite,
    redeem_invite,
    revoke_invite,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/invites", tags=["invites"])


class CreateInviteBody(BaseModel):
    match_id: str
    role: str = Field(description="judge | commentator")
    ttl_seconds: int | None = None


class RedeemBody(BaseModel):
    token: str


class RevokeBody(BaseModel):
    invite_id: str | None = None
    token: str | None = None


@router.post("")
def post_create_invite(body: CreateInviteBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            created = create_invite(
                uow,
                match_id=body.match_id,
                role=body.role,
                ttl_seconds=body.ttl_seconds,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InviteError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return created.to_public_dict()


@router.post("/redeem")
def post_redeem_invite(body: RedeemBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            redeemed = redeem_invite(uow, raw_token=body.token)
    except InviteError as exc:
        status = 404 if exc.code == "not_found" else 403
        raise HTTPException(status_code=status, detail=exc.message) from exc
    return redeemed.to_public_dict()


@router.post("/revoke")
def post_revoke_invite(body: RevokeBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            invite = revoke_invite(
                uow,
                invite_id=body.invite_id,
                raw_token=body.token,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InviteError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return {
        "invite_id": invite.id,
        "revoked": True,
        "revoked_at": invite.revoked_at.isoformat() if invite.revoked_at else None,
    }
