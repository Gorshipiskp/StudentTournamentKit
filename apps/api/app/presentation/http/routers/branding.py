"""Tournament branding API — metadata + public logo/bg assets."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select

from app.application.commands.manage_branding import (
    BrandingError,
    get_branding,
    upsert_branding,
)
from app.application.commands.rebuild_overlay import rebuild_overlay_snapshot
from app.infrastructure.persistence import models
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.deps.organizer_auth import RequireOrganizer

router = APIRouter(prefix="/api/v1/tournaments", tags=["branding"])


@router.get("/{tournament_id}/branding")
def get_branding_meta(tournament_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            branding = get_branding(uow, tournament_id=tournament_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if branding is None:
        return {
            "tournament_id": tournament_id,
            "colors": {},
            "has_logo": False,
            "has_bg": False,
            "logo_content_type": None,
            "bg_content_type": None,
        }
    return branding.to_public_meta()


@router.put("/{tournament_id}/branding")
async def put_branding(
    tournament_id: str,
    _session: RequireOrganizer,
    colors: str | None = Form(default=None),
    logo: UploadFile | None = File(default=None),
    bg: UploadFile | None = File(default=None),
    clear_logo: bool = Form(default=False),
    clear_bg: bool = Form(default=False),
) -> dict[str, Any]:
    colors_dict: dict[str, Any] | None = None
    if colors is not None and colors.strip():
        try:
            parsed = json.loads(colors)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="colors must be JSON") from exc
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=400, detail="colors must be object")
        colors_dict = parsed

    logo_bytes: bytes | None = None
    logo_ctype: str | None = None
    if logo is not None and logo.filename:
        logo_bytes = await logo.read()
        logo_ctype = logo.content_type

    bg_bytes: bytes | None = None
    bg_ctype: str | None = None
    if bg is not None and bg.filename:
        bg_bytes = await bg.read()
        bg_ctype = bg.content_type

    try:
        with SqlAlchemyUnitOfWork() as uow:
            branding = upsert_branding(
                uow,
                tournament_id=tournament_id,
                colors=colors_dict,
                logo_bytes=logo_bytes,
                logo_content_type=logo_ctype,
                clear_logo=clear_logo,
                bg_bytes=bg_bytes,
                bg_content_type=bg_ctype,
                clear_bg=clear_bg,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BrandingError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    # Refresh overlay snapshots so GET/WS include branding
    with SqlAlchemyUnitOfWork() as uow:
        match_ids = uow.session.scalars(
            select(models.Match.id).where(models.Match.tournament_id == tournament_id)
        ).all()
        for mid in match_ids:
            match = uow.matches.get(mid)
            if match is not None:
                rebuild_overlay_snapshot(uow, match, notify=True)
        if match_ids:
            uow.commit()

    return branding.to_public_meta()


@router.get("/{tournament_id}/branding/logo")
def get_logo(tournament_id: str) -> Response:
    """Public asset for overlay Browser Source (no organizer auth)."""
    with SqlAlchemyUnitOfWork() as uow:
        if uow.tournaments.get(tournament_id) is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        branding = uow.branding.get(tournament_id)
    if branding is None or not branding.logo_blob:
        raise HTTPException(status_code=404, detail="logo not found")
    return Response(
        content=branding.logo_blob,
        media_type=branding.logo_content_type or "image/png",
        headers={"Cache-Control": "public, max-age=60"},
    )


@router.get("/{tournament_id}/branding/bg")
def get_bg(tournament_id: str) -> Response:
    """Public asset for overlay Browser Source (no organizer auth)."""
    with SqlAlchemyUnitOfWork() as uow:
        if uow.tournaments.get(tournament_id) is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        branding = uow.branding.get(tournament_id)
    if branding is None or not branding.bg_blob:
        raise HTTPException(status_code=404, detail="bg not found")
    return Response(
        content=branding.bg_blob,
        media_type=branding.bg_content_type or "image/png",
        headers={"Cache-Control": "public, max-age=60"},
    )
