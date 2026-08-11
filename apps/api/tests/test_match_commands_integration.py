"""Integration: Platform commands → Fake CS2 ack (MySQL + in-process Fake)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.main import app

# tools/fake-cs2 on path
_FAKE_ROOT = Path(__file__).resolve().parents[3] / "tools" / "fake-cs2"
if str(_FAKE_ROOT) not in sys.path:
    sys.path.insert(0, str(_FAKE_ROOT))


def _configure_host_mysql() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3307")
    os.environ.setdefault("MYSQL_USER", "stk")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stk_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stk")
    reset_engine_cache()
    reset_session_factory_cache()


@pytest.fixture(scope="module")
def mysql_ready() -> None:
    _configure_host_mysql()
    if not check_database():
        pytest.skip("MySQL not reachable (start infra/platform compose)")


@pytest.fixture
def client(mysql_ready: None) -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_server():
    from fake_cs2.config import FakeConfig
    from fake_cs2.events import EventEmitter
    from fake_cs2.server import FakeHttpServer
    from fake_cs2.state import MatchState

    match_id = f"m_{uuid4().hex[:10]}"
    config = FakeConfig(
        platform_url="http://127.0.0.1:8000",
        match_id=match_id,
        server_id="srv_fake",
        webhook_secret="dev_webhook_secret_change_me",
        listen_host="127.0.0.1",
        listen_port=27201,
        dry_run=True,
    )
    state = MatchState(
        match_id=match_id,
        server_id=config.server_id,
        map_name="de_mirage",
    )
    state.apply_command(
        command_id="boot-load",
        command_type="LoadMatch",
        payload={"map": "de_mirage"},
    )
    emitter = EventEmitter(config, state)
    server = FakeHttpServer(config, state, emitter)
    server.start(background=True)
    try:
        yield {
            "match_id": match_id,
            "base": f"http://{config.listen_host}:{config.listen_port}",
            "secret": config.webhook_secret,
            "server_id": config.server_id,
        }
    finally:
        server.stop()


def test_pause_resume_forfeit_via_api_and_fake(client: TestClient, fake_server: dict) -> None:
    match_id = fake_server["match_id"]
    created = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": fake_server["server_id"],
            "webhook_secret": fake_server["secret"],
            "game_endpoint_url": fake_server["base"],
            "map_name": "de_mirage",
        },
    )
    assert created.status_code == 200, created.text

    pause = client.post(
        f"/api/v1/matches/{match_id}/commands/pause",
        json={"command_id": f"itest-pause-{uuid4().hex[:8]}", "reason": "tech"},
    )
    assert pause.status_code == 200, pause.text
    body = pause.json()
    assert body["confirmed"] is True
    assert body["status"] == "confirmed"
    assert body["match"]["desired_paused"] is True
    assert body["match"]["actual_paused"] is True
    assert body["match"]["split_brain"] is False
    assert body["http_200_means_applied"] is False

    cmd_id = body["command_id"]
    # Idempotent replay
    pause2 = client.post(
        f"/api/v1/matches/{match_id}/commands/pause",
        json={"command_id": cmd_id},
    )
    assert pause2.status_code == 200
    assert pause2.json()["idempotent_replay"] is True

    got = client.get(f"/api/v1/matches/{match_id}")
    assert got.json()["desired_paused"] is True
    assert got.json()["actual_paused"] is True

    resume = client.post(
        f"/api/v1/matches/{match_id}/commands/resume",
        json={"command_id": f"itest-resume-{uuid4().hex[:8]}"},
    )
    assert resume.status_code == 200
    assert resume.json()["confirmed"] is True
    assert resume.json()["match"]["desired_paused"] is False
    assert resume.json()["match"]["actual_paused"] is False

    ff = client.post(
        f"/api/v1/matches/{match_id}/commands/forfeit",
        json={
            "command_id": f"itest-ff-{uuid4().hex[:8]}",
            "losing_team": "team_b",
        },
    )
    assert ff.status_code == 200, ff.text
    assert ff.json()["confirmed"] is True
    assert ff.json()["match"]["status"] == "forfeited"
