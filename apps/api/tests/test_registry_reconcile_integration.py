"""Integration: assign Fake server + reconcile after drift (MySQL)."""

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
        pytest.skip("MySQL not reachable")


@pytest.fixture
def client(mysql_ready: None) -> TestClient:
    return TestClient(app)


def test_assign_and_reconcile_via_fake(client: TestClient) -> None:
    from fake_cs2.config import FakeConfig
    from fake_cs2.events import EventEmitter
    from fake_cs2.server import FakeHttpServer
    from fake_cs2.state import MatchState

    match_id = f"m_{uuid4().hex[:10]}"
    server_id = f"srv_{uuid4().hex[:8]}"
    secret = "dev_webhook_secret_change_me"
    port = 27203

    config = FakeConfig(
        platform_url="http://127.0.0.1:8000",
        match_id=match_id,
        server_id=server_id,
        webhook_secret=secret,
        listen_host="127.0.0.1",
        listen_port=port,
        dry_run=True,
        map_name="de_inferno",
    )
    state = MatchState(
        match_id=match_id, server_id=server_id, map_name="de_inferno"
    )
    state.apply_command(
        command_id="boot",
        command_type="LoadMatch",
        payload={"map": "de_inferno"},
    )
    # Advance Fake ahead of Platform (missed events)
    state.start_round(phase="buy")
    state.end_round(winner="team_a")
    state.start_round(phase="buy")
    state.end_round(winner="team_a")
    state.start_round(phase="buy")
    state.end_round(winner="team_b")
    # Fake score 2-1, last_sequence still 0 on Fake until events emitted —
    # bump sequence via emit dry-run to set last_sequence in state
    emitter = EventEmitter(config, state)
    # Force last_sequence to reflect rounds for snapshot
    state.last_sequence = 6
    server = FakeHttpServer(config, state, emitter)
    server.start(background=True)
    try:
        srv = client.post(
            "/api/v1/game-servers",
            json={
                "server_id": server_id,
                "endpoint_url": f"http://127.0.0.1:{port}",
                "webhook_secret": secret,
                "host": "127.0.0.1",
                "port": port,
            },
        )
        assert srv.status_code == 200, srv.text
        assert srv.json()["status"] == "available"

        created = client.post("/api/v1/matches", json={"match_id": match_id})
        assert created.status_code == 200

        assigned = client.post(
            f"/api/v1/matches/{match_id}/assign-server",
            json={"server_id": server_id},
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["game_server_id"] == server_id
        assert assigned.json()["status"] == "server_assigned"
        assert "27099" not in (assigned.json().get("game_endpoint_url") or "")
        assert assigned.json()["game_endpoint_url"].endswith(f":{port}")

        listed = client.get("/api/v1/game-servers")
        assert any(i["id"] == server_id for i in listed.json()["items"])
        got_srv = client.get(f"/api/v1/game-servers/{server_id}")
        assert got_srv.json()["status"] == "assigned"
        assert got_srv.json()["assigned_match_id"] == match_id

        # Platform still 0-0 — reconcile from Fake snapshot
        recon = client.post(f"/api/v1/matches/{match_id}/reconcile")
        assert recon.status_code == 200, recon.text
        body = recon.json()
        assert body["ok"] is True
        assert body["match"]["score"] == {"team_a": 2, "team_b": 1}
        assert body["match"]["round"] == 3
        assert body["match"]["map"] == "de_inferno"
        assert body["match"]["reconcile_needed"] is False

        plat = client.get(f"/api/v1/matches/{match_id}/snapshot")
        assert plat.json()["score"]["team_a"] == 2
        assert plat.json()["source"] == "platform"
    finally:
        server.stop()
