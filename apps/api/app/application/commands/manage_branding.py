"""Upsert tournament branding; size / type checks."""

from __future__ import annotations

from typing import Any

from app.application.unit_of_work import UnitOfWork
from app.domain.tournament.branding_entities import (
    ALLOWED_IMAGE_TYPES,
    BG_MAX_BYTES,
    LOGO_MAX_BYTES,
    TournamentBranding,
)


class BrandingError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _require_tournament(uow: UnitOfWork, tournament_id: str) -> None:
    if uow.tournaments.get(tournament_id) is None:
        raise KeyError(f"tournament not found: {tournament_id}")


def get_branding(uow: UnitOfWork, *, tournament_id: str) -> TournamentBranding | None:
    _require_tournament(uow, tournament_id)
    return uow.branding.get(tournament_id)


def upsert_branding(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    colors: dict[str, Any] | None = None,
    logo_bytes: bytes | None = None,
    logo_content_type: str | None = None,
    clear_logo: bool = False,
    bg_bytes: bytes | None = None,
    bg_content_type: str | None = None,
    clear_bg: bool = False,
) -> TournamentBranding:
    _require_tournament(uow, tournament_id)
    current = uow.branding.get(tournament_id) or TournamentBranding(tournament_id=tournament_id)

    if colors is not None:
        cleaned: dict[str, Any] = {}
        for key in ("primary", "accent"):
            val = colors.get(key)
            if val is None or val == "":
                continue
            text = str(val).strip()
            if not text.startswith("#") or len(text) not in (4, 7):
                raise BrandingError(f"invalid color {key}: use #RGB or #RRGGBB", code="bad_color")
            cleaned[key] = text
        current.colors_json = cleaned

    if clear_logo:
        current.logo_blob = None
        current.logo_content_type = None
    elif logo_bytes is not None:
        if len(logo_bytes) > LOGO_MAX_BYTES:
            raise BrandingError(
                f"logo exceeds {LOGO_MAX_BYTES} bytes",
                code="logo_too_large",
            )
        ctype = (logo_content_type or "image/png").split(";")[0].strip().lower()
        if ctype not in ALLOWED_IMAGE_TYPES:
            raise BrandingError(f"unsupported logo type: {ctype}", code="bad_type")
        current.logo_blob = logo_bytes
        current.logo_content_type = ctype

    if clear_bg:
        current.bg_blob = None
        current.bg_content_type = None
    elif bg_bytes is not None:
        if len(bg_bytes) > BG_MAX_BYTES:
            raise BrandingError(
                f"bg exceeds {BG_MAX_BYTES} bytes",
                code="bg_too_large",
            )
        ctype = (bg_content_type or "image/png").split(";")[0].strip().lower()
        if ctype not in ALLOWED_IMAGE_TYPES:
            raise BrandingError(f"unsupported bg type: {ctype}", code="bad_type")
        current.bg_blob = bg_bytes
        current.bg_content_type = ctype

    uow.branding.upsert(current)
    uow.commit()
    return current
