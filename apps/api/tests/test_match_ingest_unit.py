"""Unit: Match apply + ingest dedup (in-memory)."""

from __future__ import annotations

from app.application.commands.create_match import create_match
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.domain.match.apply import apply_game_event
from app.domain.match.entities import MATCH_LIVE, Match
from app.domain.match.events import MATCH_SCORE_UPDATED, MATCH_STATUS_CHANGED
from tests.fakes import InMemoryUnitOfWork


def test_apply_round_end_updates_score_and_status() -> None:
    match = Match(id="m1", tournament_id="t1", game_server_id="srv1")
    r1 = apply_game_event(
        match,
        event_type="match_loaded",
        sequence=1,
        payload={"map": "de_mirage"},
        server_id="srv1",
    )
    assert r1.applied
    assert match.map_name == "de_mirage"

    r2 = apply_game_event(
        match,
        event_type="round_end",
        sequence=2,
        payload={
            "round": 1,
            "score": {"team_a": 1, "team_b": 0},
            "map": "de_mirage",
        },
        server_id="srv1",
    )
    assert r2.applied
    assert r2.score_changed
    assert match.status == MATCH_LIVE
    assert match.score_team_a == 1
    assert match.last_sequence == 2


def test_out_of_order_does_not_overwrite_score() -> None:
    match = Match(id="m1", tournament_id="t1", last_sequence=2, score_team_a=2)
    result = apply_game_event(
        match,
        event_type="round_end",
        sequence=1,
        payload={"round": 1, "score": {"team_a": 99, "team_b": 0}},
    )
    assert not result.applied
    assert result.reason == "out_of_order"
    assert match.reconcile_needed is True
    assert match.score_team_a == 2


def test_sequence_rewind_after_bridge_restart_applies() -> None:
    """Bridge restart resets counter (371 → 12); must not drop live score events."""
    match = Match(
        id="m1",
        tournament_id="t1",
        last_sequence=371,
        score_team_a=0,
        score_team_b=1,
        round_number=2,
    )
    result = apply_game_event(
        match,
        event_type="round_end",
        sequence=12,
        payload={"round": 3, "score": {"team_a": 0, "team_b": 2}},
    )
    assert result.applied
    assert match.score_team_b == 2
    assert match.round_number == 3
    assert match.last_sequence == 12
    assert match.reconcile_needed is True


def test_ingest_happy_path_and_duplicate_event_id() -> None:
    uow = InMemoryUnitOfWork()
    match = create_match(
        uow,
        match_id="m_dev",
        game_server_id="srv_fake",
        webhook_secret="secret",
    )
    assert match.id == "m_dev"

    first = ingest_cs2_event(
        uow,
        event_id="evt-1",
        sequence=1,
        server_id="srv_fake",
        match_id="m_dev",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 1, "team_b": 0}},
        correlation_id="c1",
    )
    uow.commit()
    assert first["applied"] is True
    assert first["match"]["score"]["team_a"] == 1
    assert any(
        m.event_type == MATCH_SCORE_UPDATED for m in uow.outbox.items.values()
    )
    assert any(
        m.event_type == MATCH_STATUS_CHANGED for m in uow.outbox.items.values()
    )

    dup = ingest_cs2_event(
        uow,
        event_id="evt-1",
        sequence=1,
        server_id="srv_fake",
        match_id="m_dev",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 1, "team_b": 0}},
    )
    assert dup["status"] == "duplicate"
    assert dup["applied"] is False
    assert uow.matches.get("m_dev").score_team_a == 1


def test_domain_has_no_matchzy_rcon_strings() -> None:
    import app.domain.match.apply as apply_mod
    import inspect

    src = inspect.getsource(apply_mod)
    assert "MatchZy" not in src
    assert "RCON" not in src
    assert "mp_pause" not in src
