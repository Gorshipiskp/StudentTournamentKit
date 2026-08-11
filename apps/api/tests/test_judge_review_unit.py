"""Unit: judge review request → pause arm → continue/forfeit/cancel."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from app.application.commands.create_match import create_match
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.application.commands.judge_review import (
    JudgeConflict,
    cancel_review,
    request_review,
    resolve_review,
)
from app.domain.match.entities import MATCH_COMPLETED, MATCH_LIVE
from app.domain.match.review import (
    RESOLUTION_CONTINUE,
    RESOLUTION_FORFEIT,
    REVIEW_CANCELLED,
    REVIEW_PAUSED,
    REVIEW_REQUESTED,
    REVIEW_RESOLVED,
)
from app.infrastructure.adapters.cs2.command_client import CommandAck
from tests.fakes import InMemoryUnitOfWork


class ScriptedTransport:
    def __init__(self, acks: list[CommandAck] | None = None) -> None:
        self.acks = list(acks or [])
        self.calls: list[dict[str, Any]] = []

    def send(self, **kwargs: Any) -> CommandAck:
        self.calls.append(kwargs)
        if self.acks:
            return self.acks.pop(0)
        # default success shaped by command type
        ctype = kwargs.get("command_type")
        if ctype == "PauseMatch":
            return CommandAck(200, "confirmed", None, {"paused": True})
        if ctype == "ResumeMatch":
            return CommandAck(200, "confirmed", None, {"paused": False})
        if ctype == "ForfeitMatch":
            return CommandAck(
                200,
                "confirmed",
                None,
                {"completed": True, "score": {"team_a": 13, "team_b": 0}},
            )
        return CommandAck(200, "failed", "unknown", None)


def _live_match(uow: InMemoryUnitOfWork, match_id: str = "m_j") -> None:
    create_match(
        uow,
        match_id=match_id,
        game_server_id="srv",
        game_endpoint_url="http://127.0.0.1:27099",
    )
    m = uow.matches.get(match_id)
    assert m is not None
    m.status = MATCH_LIVE
    uow.matches.save(m)


def test_cancel_before_pause() -> None:
    uow = InMemoryUnitOfWork()
    _live_match(uow)
    request_review(uow, match_id="m_j")
    m = cancel_review(uow, match_id="m_j")
    assert m.review_status == REVIEW_CANCELLED
    assert m.status == MATCH_LIVE


def test_continue_path_arms_pause_on_round_start_buy() -> None:
    uow = InMemoryUnitOfWork()
    _live_match(uow)
    transport = ScriptedTransport()
    request_review(uow, match_id="m_j")
    assert uow.matches.get("m_j").review_status == REVIEW_REQUESTED

    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_j",
        event_type="round_start",
        payload={"round": 3, "phase": "buy"},
        transport=transport,
    )
    uow.commit()
    m = uow.matches.get("m_j")
    assert m is not None
    assert m.review_status == REVIEW_PAUSED
    assert m.status == MATCH_LIVE  # F3: tech pause ≠ MatchStatus
    assert m.desired_paused is True
    assert m.actual_paused is True
    assert m.to_public_dict()["judge_banner"] == "tech_pause"
    assert any(c["command_type"] == "PauseMatch" for c in transport.calls)

    version = m.version
    out = resolve_review(
        uow,
        match_id="m_j",
        action=RESOLUTION_CONTINUE,
        expected_version=version,
        transport=transport,
    )
    assert out["match"]["review_status"] == REVIEW_RESOLVED
    assert out["match"]["review_resolution"] == RESOLUTION_CONTINUE
    assert out["match"]["status"] == MATCH_LIVE
    assert out["match"]["desired_paused"] is False
    assert out["match"]["actual_paused"] is False


def test_forfeit_path() -> None:
    uow = InMemoryUnitOfWork()
    _live_match(uow, "m_ff")
    transport = ScriptedTransport()
    request_review(uow, match_id="m_ff")
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_ff",
        event_type="round_start",
        payload={"round": 1, "phase": "buy"},
        transport=transport,
    )
    uow.commit()
    m = uow.matches.get("m_ff")
    assert m is not None and m.review_status == REVIEW_PAUSED
    out = resolve_review(
        uow,
        match_id="m_ff",
        action=RESOLUTION_FORFEIT,
        expected_version=m.version,
        losing_team="team_b",
        transport=transport,
    )
    assert out["match"]["review_status"] == REVIEW_RESOLVED
    assert out["match"]["review_resolution"] == RESOLUTION_FORFEIT
    assert out["match"]["status"] == "forfeited"


def test_stale_resolve_on_completed_and_version_race() -> None:
    uow = InMemoryUnitOfWork()
    _live_match(uow, "m_race")
    transport = ScriptedTransport()
    request_review(uow, match_id="m_race")
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_race",
        event_type="round_start",
        payload={"round": 1, "phase": "buy"},
        transport=transport,
    )
    uow.commit()
    m = uow.matches.get("m_race")
    assert m is not None
    old_version = m.version

    # concurrent bump (e.g. another writer)
    m.version += 1
    uow.matches.save(m)

    with pytest.raises(JudgeConflict, match="version conflict"):
        resolve_review(
            uow,
            match_id="m_race",
            action=RESOLUTION_CONTINUE,
            expected_version=old_version,
            transport=transport,
        )

    # finish match then stale resolve
    m2 = uow.matches.get("m_race")
    assert m2 is not None
    m2.status = MATCH_COMPLETED
    m2.review_status = REVIEW_PAUSED
    uow.matches.save(m2)
    with pytest.raises(JudgeConflict, match="stale resolve"):
        resolve_review(
            uow,
            match_id="m_race",
            action=RESOLUTION_CONTINUE,
            expected_version=m2.version,
            transport=transport,
        )


def test_round_start_live_phase_does_not_arm() -> None:
    uow = InMemoryUnitOfWork()
    _live_match(uow, "m_liveph")
    transport = ScriptedTransport()
    request_review(uow, match_id="m_liveph")
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_liveph",
        event_type="round_start",
        payload={"round": 1, "phase": "live"},
        transport=transport,
    )
    assert uow.matches.get("m_liveph").review_status == REVIEW_REQUESTED
    assert transport.calls == []
