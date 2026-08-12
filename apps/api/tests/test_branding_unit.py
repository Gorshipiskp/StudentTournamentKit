"""Unit: branding size reject + overlay merge fields."""

from __future__ import annotations

import pytest

from app.application.commands.create_match import create_match
from app.application.commands.create_tournament_draft import create_tournament_draft
from app.application.commands.manage_branding import BrandingError, upsert_branding
from app.application.commands.rebuild_overlay import get_overlay_message, rebuild_overlay_snapshot
from app.domain.overlay.merge_policy import merge_overlay_data
from app.domain.tournament.branding_entities import LOGO_MAX_BYTES
from tests.fakes import InMemoryUnitOfWork

# 1x1 PNG
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_merge_includes_branding_and_keeps_watermark() -> None:
    data = merge_overlay_data(
        match_public={
            "score": {"team_a": 1, "team_b": 0},
            "round": 1,
            "map": None,
            "phase": "live",
            "status": "live",
            "actual_paused": False,
            "review_status": "none",
            "judge_banner": None,
        },
        desired_scene="ingame",
        branding={
            "logo_url": "/api/v1/tournaments/t1/branding/logo",
            "bg_url": None,
            "colors": {"primary": "#112233"},
        },
    )
    assert data["watermark"]["visible"] is True
    assert data["branding"]["logo_url"].endswith("/logo")
    assert data["branding"]["colors"]["primary"] == "#112233"


def test_logo_too_large_rejected() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    with pytest.raises(BrandingError, match="exceeds"):
        upsert_branding(
            uow,
            tournament_id=tid,
            logo_bytes=b"x" * (LOGO_MAX_BYTES + 1),
            logo_content_type="image/png",
        )


def test_upload_then_overlay_has_branding() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_brand")
    upsert_branding(
        uow,
        tournament_id=tid,
        colors={"primary": "#3d9a86", "accent": "#c9a227"},
        logo_bytes=_TINY_PNG,
        logo_content_type="image/png",
    )
    rebuild_overlay_snapshot(uow, match, notify=False)
    msg = get_overlay_message(uow, match.id)
    assert msg is not None
    branding = msg["data"]["branding"]
    assert branding["logo_url"] == f"/api/v1/tournaments/{tid}/branding/logo"
    assert branding["colors"]["primary"] == "#3d9a86"
    assert msg["data"]["watermark"]["visible"] is True
