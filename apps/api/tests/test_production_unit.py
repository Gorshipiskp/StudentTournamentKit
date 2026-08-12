"""Unit: production PATCH + outbox notify agent hub (fake agent queue)."""

from __future__ import annotations

import asyncio

from app.application.commands.create_match import create_match
from app.application.commands.rebuild_overlay import get_overlay_message
from app.application.commands.update_production import (
    ProductionConflict,
    apply_agent_actual,
    get_production,
    patch_production,
)
from app.domain.production.entities import PRODUCTION_DESIRED_CHANGED
from app.domain.production.messages import TYPE_PRODUCTION_DESIRED
from app.infrastructure.outbox.dispatcher import handle_outbox_message
from app.infrastructure.realtime.agent_hub import AgentHub
from tests.fakes import InMemoryUnitOfWork
import pytest


def test_patch_desired_scene_persists_and_bumps_overlay() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_prod", game_server_id="srv")
    before = get_overlay_message(uow, "m_prod")
    assert before is not None
    assert before["data"]["scene"] == "waiting"
    v0 = before["version"]

    pub = patch_production(
        uow,
        match_id="m_prod",
        desired_scene="intro",
        correlation_id="c-prod",
    )
    assert pub["desired"]["scene"] == "intro"
    assert get_production(uow, match_id="m_prod")["desired"]["scene"] == "intro"

    after = get_overlay_message(uow, "m_prod")
    assert after is not None
    assert after["data"]["scene"] == "intro"
    assert after["version"] == v0 + 1

    assert any(
        m.event_type == PRODUCTION_DESIRED_CHANGED for m in uow.outbox.items.values()
    )


def test_patch_invalid_scene_rejected() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_bad")
    with pytest.raises(ProductionConflict):
        patch_production(uow, match_id="m_bad", desired_scene="not_a_scene")


def test_fake_agent_receives_desired_after_patch() -> None:
    """Service-level fake agent: subscribed queue gets production.desired."""
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_agent", game_server_id="srv")
    patch_production(uow, match_id="m_agent", desired_scene="ingame")

    hub = AgentHub()

    async def _run() -> None:
        queue: asyncio.Queue = asyncio.Queue()
        hub._queues["m_agent"].append(queue)

        from app.infrastructure.realtime import agent_hub as hub_mod

        original = hub_mod.agent_hub
        hub_mod.agent_hub = hub
        try:
            msgs = [
                m
                for m in uow.outbox.items.values()
                if m.event_type == PRODUCTION_DESIRED_CHANGED
            ]
            assert msgs
            handle_outbox_message(msgs[-1])
        finally:
            hub_mod.agent_hub = original

        pushed = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert pushed["type"] == TYPE_PRODUCTION_DESIRED
        assert pushed["desired"]["scene"] == "ingame"

    asyncio.run(_run())


def test_apply_agent_actual_updates_session() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_act")
    patch_production(uow, match_id="m_act", desired_scene="ingame")
    pub = apply_agent_actual(
        uow,
        match_id="m_act",
        actual_scene="ingame",
        actual_stream="off",
        obs_status="connected",
        agent_status="connected",
    )
    assert pub["actual"]["scene"] == "ingame"
    assert pub["obs_status"] == "connected"
    assert pub["agent_status"] == "connected"
