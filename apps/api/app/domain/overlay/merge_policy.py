"""Merge game view + production scene + overrides + judge → overlay data."""

from __future__ import annotations

from typing import Any

from app.domain.overlay.entities import (
    DEFAULT_TEAM_A_NAME,
    DEFAULT_TEAM_B_NAME,
    WATERMARK_TEXT,
)


def merge_overlay_data(
    *,
    match_public: dict[str, Any],
    desired_scene: str,
    manual_overrides: dict[str, Any] | None = None,
    branding: dict[str, Any] | None = None,
    tournament_name: str | None = None,
    live_fx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Priority: judge_banner > manual_overrides > game_state (score/round/map).
    Scene always from production desired.
    Watermark always visible (no disable flag).
    Branding is additive (logo_url / colors) — never hides watermark.
    live_fx is ephemeral broadcast chrome (bomb / round win); optional.
    """
    overrides = dict(manual_overrides or {})
    score = match_public.get("score") or {}
    team_a_score = int(score.get("team_a", 0))
    team_b_score = int(score.get("team_b", 0))
    if "score_team_a" in overrides:
        team_a_score = int(overrides["score_team_a"])
    if "score_team_b" in overrides:
        team_b_score = int(overrides["score_team_b"])

    team_a_name = str(overrides.get("team_a_name") or DEFAULT_TEAM_A_NAME)
    team_b_name = str(overrides.get("team_b_name") or DEFAULT_TEAM_B_NAME)

    judge_status = str(match_public.get("review_status") or "none")
    banner = match_public.get("judge_banner")
    if "judge_banner" in overrides:
        banner = overrides["judge_banner"]

    map_name = match_public.get("map")
    if "map" in overrides:
        map_name = overrides["map"]

    round_number = int(match_public.get("round") or 0)
    if "round" in overrides:
        round_number = int(overrides["round"])

    data: dict[str, Any] = {
        "scene": desired_scene,
        "team_a": {"name": team_a_name, "score": team_a_score},
        "team_b": {"name": team_b_name, "score": team_b_score},
        "map": map_name,
        "round": round_number,
        "phase": match_public.get("phase"),
        "match_status": match_public.get("status"),
        "paused": bool(match_public.get("actual_paused")),
        "judge": {"status": judge_status, "banner": banner},
        "watermark": {"text": WATERMARK_TEXT, "visible": True},
    }
    if tournament_name:
        data["tournament_name"] = tournament_name
    if branding:
        data["branding"] = branding
    if live_fx:
        data["fx"] = live_fx
    return data
