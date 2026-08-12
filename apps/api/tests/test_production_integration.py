"""Integration: PATCH production + fake agent WS receives desired."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.infrastructure.realtime.agent_auth import DEFAULT_DEV_TOKEN
from app.main import app


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


def test_patch_production_and_fake_agent_ws(client: TestClient) -> None:
    match_id = f"m_prod_{uuid4().hex[:10]}"
    created = client.post(
        "/api/v1/matches",
        json={"match_id": match_id, "game_server_id": "srv_prod"},
    )
    assert created.status_code == 200, created.text

    got = client.get(f"/api/v1/matches/{match_id}/production")
    assert got.status_code == 200
    assert got.json()["desired"]["scene"] == "waiting"

    # Fake agent connects before PATCH so it receives push
    with client.websocket_connect(
        f"/ws/agent/{match_id}?token={DEFAULT_DEV_TOKEN}"
    ) as ws:
        initial = ws.receive_json()
        assert initial["type"] == "production.desired"
        assert initial["desired"]["scene"] == "waiting"

        patched = client.patch(
            f"/api/v1/matches/{match_id}/production",
            json={"desired_scene": "intro"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["desired"]["scene"] == "intro"

        pushed = ws.receive_json()
        assert pushed["type"] == "production.desired"
        assert pushed["desired"]["scene"] == "intro"

        # Agent reports actual (no OBS — fake)
        ws.send_json(
            {
                "type": "production.actual",
                "actual": {"scene": "intro", "stream": "off"},
                "obs_status": "connected",
            }
        )
        ack = ws.receive_json()
        assert ack["type"] == "production.actual_ack"
        assert ack["actual"]["scene"] == "intro"

    after = client.get(f"/api/v1/matches/{match_id}/production")
    assert after.json()["desired"]["scene"] == "intro"
    assert after.json()["actual"]["scene"] == "intro"

    # Overlay scene follows desired
    ov = client.get(f"/api/v1/matches/{match_id}/overlay")
    assert ov.status_code == 200
    assert ov.json()["data"]["scene"] == "intro"


def test_agent_ws_rejects_bad_token(client: TestClient) -> None:
    match_id = f"m_tok_{uuid4().hex[:8]}"
    client.post("/api/v1/matches", json={"match_id": match_id})
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/agent/{match_id}?token=wrong"):
            pass
