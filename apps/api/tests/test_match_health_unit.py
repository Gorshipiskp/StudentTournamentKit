"""Unit: match health aggregate (Fake OBS / Fake game)."""

from __future__ import annotations

from app.application.commands.create_match import create_match
from app.application.commands.get_match_health import (
    DEGRADED,
    HEALTHY,
    OFFLINE,
    UNKNOWN,
    get_match_health,
)
from app.application.commands.start_match import start_match_fake
from app.application.commands.update_production import apply_agent_actual
from tests.fakes import InMemoryUnitOfWork
import pytest


def test_health_offline_before_agent() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_h1", game_server_id="srv_fake")
    body = get_match_health(uow, match_id="m_h1")
    assert body["match_id"] == "m_h1"
    assert body["components"]["platform"]["status"] == HEALTHY
    assert body["components"]["agent"]["status"] == OFFLINE
    assert body["components"]["obs"]["status"] == OFFLINE
    assert body["components"]["game_server"]["mode"] == "fake"
    assert body["components"]["game_server"]["status"] == HEALTHY
    assert body["components"]["broadcast"]["status"] == UNKNOWN
    assert body["overall"] == OFFLINE


def test_health_healthy_after_fake_obs_connect() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_h2", game_server_id="srv_fake", map_name="de_mirage")
    start_match_fake(uow, match_id="m_h2", correlation_id="c-h")
    apply_agent_actual(
        uow,
        match_id="m_h2",
        actual_scene="ingame",
        actual_stream="off",
        obs_status="connected",
        agent_status="connected",
        broadcast_status="idle",
    )
    body = get_match_health(uow, match_id="m_h2")
    assert body["components"]["agent"]["status"] == HEALTHY
    assert body["components"]["obs"]["status"] == HEALTHY
    assert body["components"]["overlay"]["status"] == HEALTHY
    assert body["components"]["overlay"]["revision"] >= 1
    assert body["components"]["game_server"]["status"] == HEALTHY
    assert body["components"]["broadcast"]["status"] == HEALTHY
    assert body["overall"] == HEALTHY
    assert body["production"]["agent_status"] == "connected"
    assert body["production"]["obs_status"] == "connected"


def test_health_degraded_when_obs_down_agent_up() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_h3", game_server_id="srv_fake")
    apply_agent_actual(
        uow,
        match_id="m_h3",
        obs_status="disconnected",
        agent_status="connected",
    )
    body = get_match_health(uow, match_id="m_h3")
    assert body["components"]["agent"]["status"] == HEALTHY
    assert body["components"]["obs"]["status"] == OFFLINE
    assert body["overall"] == OFFLINE


def test_health_unknown_match() -> None:
    uow = InMemoryUnitOfWork()
    with pytest.raises(KeyError):
        get_match_health(uow, match_id="missing")


def test_health_agent_degraded() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_h4", game_server_id="srv_fake")
    apply_agent_actual(
        uow,
        match_id="m_h4",
        agent_status="degraded",
        obs_status="connected",
    )
    body = get_match_health(uow, match_id="m_h4")
    assert body["components"]["agent"]["status"] == DEGRADED
    assert body["overall"] == DEGRADED
