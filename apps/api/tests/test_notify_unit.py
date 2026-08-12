"""API-level: judge review → overlay.updated + match.status fanout."""

from __future__ import annotations

from app.application.commands.create_match import create_match
from app.application.commands.judge_review import (
    cancel_review,
    request_review,
    resolve_review,
)
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.domain.match.entities import MATCH_LIVE
from app.domain.match.messages import (
    JUDGE_REVIEW_REQUESTED,
    JUDGE_REVIEW_RESOLVED,
    JUDGE_REVIEW_TECH_PAUSE,
    TYPE_MATCH_STATUS,
)
from app.domain.overlay.entities import OVERLAY_UPDATED
from app.infrastructure.adapters.cs2.command_client import CommandAck
from app.infrastructure.outbox.dispatcher import handle_outbox_message
from app.infrastructure.realtime.judge_hub import judge_hub
from app.infrastructure.realtime.overlay_hub import overlay_hub
from tests.fakes import InMemoryUnitOfWork
from tests.test_judge_review_unit import ScriptedTransport


def _live(uow: InMemoryUnitOfWork, match_id: str = "m_n") -> None:
    create_match(
        uow,
        match_id=match_id,
        game_server_id="srv",
        game_endpoint_url="http://127.0.0.1:27099",
        webhook_secret="s",
    )
    m = uow.matches.get(match_id)
    assert m is not None
    m.status = MATCH_LIVE
    uow.matches.save(m)


def test_request_review_rebuilds_overlay_and_outbox_events() -> None:
    uow = InMemoryUnitOfWork()
    _live(uow)
    before = uow.overlays.get("m_n")
    assert before is not None
    rev0 = before.revision

    request_review(uow, match_id="m_n")

    after = uow.overlays.get("m_n")
    assert after is not None
    assert after.revision == rev0 + 1
    assert after.data["judge"]["banner"] == "review_requested"

    types = {m.event_type for m in uow.outbox.items.values()}
    assert OVERLAY_UPDATED in types
    assert JUDGE_REVIEW_REQUESTED in types

    # Fanout: overlay + judge hubs
    class Q:
        def __init__(self) -> None:
            self.items: list = []

        def put_nowait(self, item) -> None:
            self.items.append(item)

    oq, jq = Q(), Q()
    overlay_hub._queues["m_n"] = [oq]  # type: ignore[attr-defined]
    judge_hub._queues["m_n"] = [jq]  # type: ignore[attr-defined]
    try:
        for msg in uow.outbox.items.values():
            handle_outbox_message(msg)
        assert any(i.get("type") == "overlay.snapshot" for i in oq.items)
        assert any(i.get("type") == TYPE_MATCH_STATUS for i in jq.items)
        status = next(i for i in jq.items if i.get("type") == TYPE_MATCH_STATUS)
        assert status["reason"] == JUDGE_REVIEW_REQUESTED
        assert status["match"]["review_status"] == "requested"
    finally:
        overlay_hub._queues.pop("m_n", None)  # type: ignore[attr-defined]
        judge_hub.reset()


def test_tech_pause_arm_notifies_and_resolve_clears_banner() -> None:
    uow = InMemoryUnitOfWork()
    _live(uow)
    request_review(uow, match_id="m_n")
    transport = ScriptedTransport(
        [
            CommandAck(200, "confirmed", None, {"paused": True}),
            CommandAck(200, "confirmed", None, {"paused": False}),
        ]
    )
    ingest_cs2_event(
        uow,
        event_id="e1",
        sequence=1,
        server_id="srv",
        match_id="m_n",
        event_type="round_start",
        payload={"round": 2, "phase": "buy"},
        transport=transport,
    )
    types = {m.event_type for m in uow.outbox.items.values()}
    assert JUDGE_REVIEW_TECH_PAUSE in types
    ov = uow.overlays.get("m_n")
    assert ov is not None
    assert ov.data["judge"]["banner"] == "tech_pause"

    m = uow.matches.get("m_n")
    assert m is not None
    resolve_review(
        uow,
        match_id="m_n",
        action="continue",
        expected_version=m.version,
        transport=transport,
    )
    types2 = {x.event_type for x in uow.outbox.items.values()}
    assert JUDGE_REVIEW_RESOLVED in types2
    ov2 = uow.overlays.get("m_n")
    assert ov2 is not None
    assert ov2.data["judge"]["banner"] is None
    assert ov2.data["judge"]["status"] == "resolved"


def test_cancel_clears_banner() -> None:
    uow = InMemoryUnitOfWork()
    _live(uow)
    request_review(uow, match_id="m_n")
    cancel_review(uow, match_id="m_n")
    ov = uow.overlays.get("m_n")
    assert ov is not None
    assert ov.data["judge"]["banner"] is None
