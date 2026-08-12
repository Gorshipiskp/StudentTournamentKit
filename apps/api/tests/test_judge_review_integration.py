"""Integration: judge review → Fake pause → continue (MySQL)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.adapters.cs2.hmac_util import sign_body
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


@pytest.fixture
def fake_and_match(client: TestClient):
    from fake_cs2.config import FakeConfig
    from fake_cs2.events import EventEmitter
    from fake_cs2.server import FakeHttpServer
    from fake_cs2.state import MatchState

    match_id = f"m_{uuid4().hex[:10]}"
    secret = "dev_webhook_secret_change_me"
    config = FakeConfig(
        platform_url="http://127.0.0.1:8000",
        match_id=match_id,
        server_id="srv_fake",
        webhook_secret=secret,
        listen_host="127.0.0.1",
        listen_port=27202,
        dry_run=True,
    )
    state = MatchState(match_id=match_id, server_id=config.server_id, map_name="de_mirage")
    state.apply_command(
        command_id="boot",
        command_type="LoadMatch",
        payload={"map": "de_mirage"},
    )
    emitter = EventEmitter(config, state)
    server = FakeHttpServer(config, state, emitter)
    server.start(background=True)
    try:
        created = client.post(
            "/api/v1/matches",
            json={
                "match_id": match_id,
                "game_server_id": config.server_id,
                "webhook_secret": secret,
                "game_endpoint_url": f"http://{config.listen_host}:{config.listen_port}",
            },
        )
        assert created.status_code == 200
        # promote to live via round_end ingest
        event = {
            "event_id": str(uuid4()),
            "sequence": 1,
            "server_id": config.server_id,
            "match_id": match_id,
            "type": "round_end",
            "timestamp": "2026-08-11T20:00:00Z",
            "payload": {"round": 1, "score": {"team_a": 1, "team_b": 0}},
        }
        raw = json.dumps(event, separators=(",", ":")).encode()
        r = client.post(
            "/api/v1/internal/cs2/events",
            content=raw,
            headers={
                "Content-Type": "application/json",
                "X-STK-Signature": sign_body(secret, raw),
            },
        )
        assert r.status_code == 200
        assert r.json()["match"]["status"] == "live"
        yield {
            "client": client,
            "match_id": match_id,
            "secret": secret,
            "server_id": config.server_id,
            "seq": 1,
        }
    finally:
        server.stop()


def test_review_continue_on_fake(fake_and_match: dict) -> None:
    client: TestClient = fake_and_match["client"]
    match_id = fake_and_match["match_id"]
    secret = fake_and_match["secret"]
    server_id = fake_and_match["server_id"]
    seq = fake_and_match["seq"]

    invite = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "judge"},
    )
    assert invite.status_code == 200, invite.text
    redeemed = client.post(
        "/api/v1/invites/redeem",
        json={"token": invite.json()["token"]},
    )
    assert redeemed.status_code == 200, redeemed.text
    headers = {"Authorization": f"Bearer {redeemed.json()['access_token']}"}

    req = client.post(
        f"/api/v1/matches/{match_id}/judge/review-request",
        headers=headers,
    )
    assert req.status_code == 200
    assert req.json()["review_status"] == "requested"
    assert req.json()["status"] == "live"

    # next round buy → Platform arms PauseMatch to Fake
    seq += 1
    event = {
        "event_id": str(uuid4()),
        "sequence": seq,
        "server_id": server_id,
        "match_id": match_id,
        "type": "round_start",
        "timestamp": "2026-08-11T20:01:00Z",
        "payload": {"round": 2, "phase": "buy"},
    }
    raw = json.dumps(event, separators=(",", ":")).encode()
    armed = client.post(
        "/api/v1/internal/cs2/events",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-STK-Signature": sign_body(secret, raw),
        },
    )
    assert armed.status_code == 200, armed.text
    body = armed.json()
    assert body["match"]["review_status"] == "paused"
    assert body["match"]["status"] == "live"
    assert body["match"]["actual_paused"] is True
    assert body.get("armed_pause", {}).get("confirmed") is True

    got = client.get(f"/api/v1/matches/{match_id}")
    version = got.json()["version"]

    resolved = client.post(
        f"/api/v1/matches/{match_id}/judge/review-resolve",
        headers=headers,
        json={"action": "continue", "version": version},
    )
    assert resolved.status_code == 200, resolved.text
    m = resolved.json()["match"]
    assert m["review_status"] == "resolved"
    assert m["review_resolution"] == "continue"
    assert m["status"] == "live"
    assert m["desired_paused"] is False
    assert m["actual_paused"] is False
