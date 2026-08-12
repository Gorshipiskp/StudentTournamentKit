"""Unit: apply_overlay_fx for lab / manual FX inject."""

from __future__ import annotations

from app.application.commands.apply_overlay_fx import apply_overlay_fx
from app.application.commands.create_match import create_match
from app.application.commands.create_tournament_draft import create_tournament_draft
from tests.fakes import InMemoryUnitOfWork


def test_apply_overlay_fx_round_win() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Lab")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_fx_lab")
    msg = apply_overlay_fx(
        uow,
        match_id=match.id,
        kind="round_win",
        side="team_a",
        round_number=5,
    )
    assert msg["data"]["fx"]["kind"] == "round_win"
    assert msg["data"]["fx"]["side"] == "team_a"
    assert msg["data"]["fx"]["label"] == "Победа CT"


def test_apply_overlay_fx_clear() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Lab")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_fx_clear")
    apply_overlay_fx(uow, match_id=match.id, kind="bomb_planted", site=1)
    msg = apply_overlay_fx(uow, match_id=match.id, clear=True)
    assert msg["data"].get("fx") in (None, {})


def test_apply_overlay_fx_unknown_kind() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Lab")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_fx_bad")
    try:
        apply_overlay_fx(uow, match_id=match.id, kind="nope")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "unknown fx kind" in str(exc)
