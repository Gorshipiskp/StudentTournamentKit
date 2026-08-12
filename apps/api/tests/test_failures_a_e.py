"""Failure scenarios A–E (INVARIANTS §16) — Fake / in-memory Game Slice."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.commands.create_match import create_match
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.application.commands.judge_review import (
    JudgeConflict,
    request_review,
    resolve_review,
)
from app.application.commands.reconcile_match import reconcile_match_from_snapshot
from app.domain.match.entities import MATCH_LIVE
from app.domain.match.review import RESOLUTION_CONTINUE, REVIEW_PAUSED
from tests.fakes import InMemoryUnitOfWork
from tests.test_judge_review_unit import ScriptedTransport, _live_match
from tests.test_registry_reconcile_unit import SnapshotTransport


def test_failure_A_platform_restart_then_reconcile() -> None:
    """A: Platform loses mid-match view; Fake continued; GetSnapshot repairs."""
    uow = InMemoryUnitOfWork()
    create_match(
        uow,
        match_id="m_a",
        game_server_id="srv",
        game_endpoint_url="http://fake",
        map_name="de_mirage",
    )
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_a",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 1, "team_b": 0}, "map": "de_mirage"},
    )
    uow.commit()
    m = uow.matches.get("m_a")
    assert m is not None
    assert m.score_team_a == 1
    assert m.last_sequence == 1

    # Simulate Platform restart with stale row + Fake ahead (missed events)
    m.reconcile_needed = True
    m.score_team_a = 1
    m.score_team_b = 0
    uow.matches.save(m)

    transport = SnapshotTransport(
        {
            "match_id": "m_a",
            "server_id": "srv",
            "map": "de_mirage",
            "round": 5,
            "score": {"team_a": 3, "team_b": 2},
            "phase": "freeze",
            "paused": False,
            "loaded": True,
            "completed": False,
            "last_sequence": 10,
            "players": [],
        }
    )
    result = reconcile_match_from_snapshot(uow, match_id="m_a", transport=transport)
    assert result["ok"] is True
    repaired = uow.matches.get("m_a")
    assert repaired is not None
    assert repaired.score_team_a == 3
    assert repaired.score_team_b == 2
    assert repaired.last_sequence == 10
    assert repaired.reconcile_needed is False


def test_failure_B_agent_restart_covered_by_director_agent() -> None:
    """B: Agent restart → apply desired, not command history (A12) — TZ003."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    reconciler_test = (
        root
        / "apps"
        / "director-agent"
        / "internal"
        / "application"
        / "reconciler_test.go"
    )
    assert reconciler_test.is_file(), (
        "Failure B requires apps/director-agent reconciler tests "
        "(TestRestartAppliesDesiredNotHistory)"
    )
    src = reconciler_test.read_text(encoding="utf-8")
    assert "TestRestartAppliesDesiredNotHistory" in src
    assert "ApplyDesired" in src


def test_failure_C_duplicate_webhook_no_double_score() -> None:
    """C: Duplicate event_id → no-op, score unchanged."""
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_c", game_server_id="srv")
    eid = str(uuid4())
    first = ingest_cs2_event(
        uow,
        event_id=eid,
        sequence=1,
        server_id="srv",
        match_id="m_c",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 2, "team_b": 0}},
    )
    uow.commit()
    assert first["applied"] is True
    dup = ingest_cs2_event(
        uow,
        event_id=eid,
        sequence=1,
        server_id="srv",
        match_id="m_c",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 99, "team_b": 0}},
    )
    assert dup["status"] == "duplicate"
    assert dup["applied"] is False
    assert uow.matches.get("m_c").score_team_a == 2


def test_failure_D_out_of_order_webhook_sets_reconcile() -> None:
    """D: OOO sequence → no overwrite + reconcile_needed."""
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_d", game_server_id="srv")
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=2,
        server_id="srv",
        match_id="m_d",
        event_type="round_end",
        payload={"round": 2, "score": {"team_a": 2, "team_b": 0}},
    )
    uow.commit()
    assert uow.matches.get("m_d").score_team_a == 2

    late = ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_d",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 99, "team_b": 0}},
    )
    uow.commit()
    assert late["applied"] is False
    assert late["reason"] == "out_of_order"
    m = uow.matches.get("m_d")
    assert m is not None
    assert m.score_team_a == 2
    assert m.reconcile_needed is True


def test_failure_E_judge_resolve_race_with_round_end() -> None:
    """E: Late round_end bumps version → resolve with stale version rejected."""
    uow = InMemoryUnitOfWork()
    _live_match(uow, "m_e")
    transport = ScriptedTransport()
    request_review(uow, match_id="m_e")
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_e",
        event_type="round_start",
        payload={"round": 2, "phase": "buy"},
        transport=transport,
    )
    uow.commit()
    m = uow.matches.get("m_e")
    assert m is not None
    assert m.review_status == REVIEW_PAUSED
    stale_version = m.version

    # Late round_end while review paused (race) — score update bumps version
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=2,
        server_id="srv",
        match_id="m_e",
        event_type="round_end",
        payload={"round": 2, "score": {"team_a": 4, "team_b": 3}},
    )
    uow.commit()
    m2 = uow.matches.get("m_e")
    assert m2 is not None
    assert m2.score_team_a == 4
    assert m2.version > stale_version
    assert m2.status == MATCH_LIVE

    with pytest.raises(JudgeConflict, match="version conflict"):
        resolve_review(
            uow,
            match_id="m_e",
            action=RESOLUTION_CONTINUE,
            expected_version=stale_version,
            transport=transport,
        )

    # Resolve with fresh version still works
    out = resolve_review(
        uow,
        match_id="m_e",
        action=RESOLUTION_CONTINUE,
        expected_version=m2.version,
        transport=transport,
    )
    assert out["match"]["review_resolution"] == "continue"
