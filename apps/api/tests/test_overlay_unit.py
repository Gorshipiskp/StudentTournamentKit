"""Unit: overlay revision bumps on Fake score; hub reconnect snapshot."""

from __future__ import annotations

import asyncio

from app.application.commands.create_match import create_match
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.application.commands.rebuild_overlay import (
    apply_overlay_override,
    get_overlay_message,
)
from app.domain.overlay.entities import OVERLAY_SNAPSHOT_TYPE, OVERLAY_UPDATED
from app.infrastructure.outbox.dispatcher import handle_outbox_message
from app.infrastructure.realtime.overlay_hub import OverlayHub
from tests.fakes import InMemoryUnitOfWork


def test_score_event_bumps_overlay_version() -> None:
    uow = InMemoryUnitOfWork()
    match = create_match(
        uow,
        match_id="m_ovl",
        game_server_id="srv_fake",
        webhook_secret="secret",
        map_name="de_mirage",
    )
    assert uow.overlays.get(match.id) is not None
    assert uow.overlays.get(match.id).revision == 1
    assert uow.production.get(match.id) is not None

    before = get_overlay_message(uow, match.id)
    assert before is not None
    assert before["type"] == OVERLAY_SNAPSHOT_TYPE
    assert before["version"] == 1
    assert before["data"]["watermark"]["visible"] is True

    ingest_cs2_event(
        uow,
        event_id="evt-score-1",
        sequence=1,
        server_id="srv_fake",
        match_id="m_ovl",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 2, "team_b": 0}, "map": "de_mirage"},
        correlation_id="c-ovl",
    )
    uow.commit()

    after = get_overlay_message(uow, "m_ovl")
    assert after is not None
    assert after["version"] == 2
    assert after["data"]["team_a"]["score"] == 2
    assert after["data"]["round"] == 1
    assert after["data"]["match_status"] == "live"
    assert any(m.event_type == OVERLAY_UPDATED for m in uow.outbox.items.values())

    # Second score → version 3
    ingest_cs2_event(
        uow,
        event_id="evt-score-2",
        sequence=2,
        server_id="srv_fake",
        match_id="m_ovl",
        event_type="round_end",
        payload={"round": 2, "score": {"team_a": 3, "team_b": 0}},
    )
    assert get_overlay_message(uow, "m_ovl")["version"] == 3


def test_hub_publish_and_reconnect_gets_full_snapshot() -> None:
    """Service-level: subscriber receives full snapshot; 'reconnect' reads DB again."""
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_ws", game_server_id="srv", webhook_secret="s")
    ingest_cs2_event(
        uow,
        event_id="e1",
        sequence=1,
        server_id="srv",
        match_id="m_ws",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 1, "team_b": 0}},
    )

    hub = OverlayHub()

    async def _run() -> None:
        queue: asyncio.Queue = asyncio.Queue()
        hub._queues["m_ws"].append(queue)

        # Simulate outbox handler push
        overlay_msgs = [
            m for m in uow.outbox.items.values() if m.event_type == OVERLAY_UPDATED
        ]
        assert overlay_msgs
        # Use real handle against our hub instance
        from app.infrastructure.realtime import overlay_hub as hub_mod

        original = hub_mod.overlay_hub
        hub_mod.overlay_hub = hub
        try:
            handle_outbox_message(overlay_msgs[-1])
        finally:
            hub_mod.overlay_hub = original

        pushed = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert pushed["type"] == OVERLAY_SNAPSHOT_TYPE
        assert pushed["version"] >= 2
        assert pushed["data"]["team_a"]["score"] == 1

        # Reconnect path: load full snapshot from store (client state irrelevant)
        reconnect = get_overlay_message(uow, "m_ws")
        assert reconnect is not None
        assert reconnect["type"] == OVERLAY_SNAPSHOT_TYPE
        assert reconnect["version"] == pushed["version"]
        assert reconnect["data"] == pushed["data"]

    asyncio.run(_run())


def test_overlay_override_bumps_version_and_names() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_ovr", game_server_id="srv")
    before = get_overlay_message(uow, "m_ovr")
    assert before is not None
    msg = apply_overlay_override(
        uow,
        match_id="m_ovr",
        patch={"team_a_name": "Alpha", "score_team_a": 9},
    )
    assert msg["version"] == before["version"] + 1
    assert msg["data"]["team_a"]["name"] == "Alpha"
    assert msg["data"]["team_a"]["score"] == 9
    cleared = apply_overlay_override(uow, match_id="m_ovr", clear=True)
    assert cleared["version"] == msg["version"] + 1
    assert cleared["data"]["team_a"]["name"] == "Team A"
