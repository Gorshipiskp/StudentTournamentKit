"""Unit tests for overlay live FX builders."""

from __future__ import annotations

from app.domain.overlay.live_fx import build_live_fx
from app.domain.overlay.merge_policy import merge_overlay_data


def test_bomb_planted_fx_has_timer():
    fx = build_live_fx("bomb_planted", {"site": 1, "timer_sec": 40}, sequence=5)
    assert fx is not None
    assert fx["kind"] == "bomb_planted"
    assert fx["timer_sec"] == 40
    assert fx["site"] == 1
    assert fx["seq"] == 5


def test_defuse_start_maps_to_bomb_defusing():
    fx = build_live_fx("bomb_defuse_start", {"has_kit": True}, sequence=6)
    assert fx is not None
    assert fx["kind"] == "bomb_defusing"
    assert fx["has_kit"] is True


def test_round_end_maps_to_round_win_side():
    fx = build_live_fx("round_end", {"winner": "team_a"}, sequence=7)
    assert fx is not None
    assert fx["kind"] == "round_win"
    assert fx["side"] == "team_a"


def test_merge_includes_fx():
    data = merge_overlay_data(
        match_public={
            "score": {"team_a": 1, "team_b": 0},
            "round": 2,
            "status": "live",
            "phase": "live",
            "actual_paused": False,
            "review_status": "none",
            "judge_banner": None,
            "map": "de_mirage",
        },
        desired_scene="ingame",
        live_fx={"kind": "bomb_planted", "label": "Бомба заложена", "ttl_ms": 1000, "seq": 1, "at": "t"},
    )
    assert data["fx"]["kind"] == "bomb_planted"
