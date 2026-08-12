"""Integration: Fake score → GET overlay version++; WS full snapshot."""

from __future__ import annotations

import json
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.adapters.cs2.hmac_util import sign_body
from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
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


def _post_round_end(client: TestClient, *, match_id: str, secret: str, server_id: str, seq: int, score_a: int) -> None:
    event = {
        "event_id": str(uuid4()),
        "sequence": seq,
        "server_id": server_id,
        "match_id": match_id,
        "type": "round_end",
        "timestamp": "2026-08-11T20:00:00Z",
        "correlation_id": "overlay-itest",
        "payload": {
            "round": seq,
            "score": {"team_a": score_a, "team_b": 0},
            "map": "de_mirage",
        },
    }
    raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-STK-Signature": sign_body(secret, raw),
        "X-STK-Event-Id": event["event_id"],
    }
    r = client.post("/api/v1/internal/cs2/events", content=raw, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["applied"] is True


def test_overlay_version_grows_after_fake_score(client: TestClient) -> None:
    secret = "dev_webhook_secret_change_me"
    match_id = f"m_ovl_{uuid4().hex[:10]}"
    server_id = "srv_fake_ovl"

    created = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": server_id,
            "webhook_secret": secret,
            "map_name": "de_mirage",
        },
    )
    assert created.status_code == 200, created.text

    ov0 = client.get(f"/api/v1/matches/{match_id}/overlay")
    assert ov0.status_code == 200, ov0.text
    body0 = ov0.json()
    assert body0["type"] == "overlay.snapshot"
    assert body0["version"] == 1
    assert body0["data"]["watermark"]["visible"] is True

    _post_round_end(
        client, match_id=match_id, secret=secret, server_id=server_id, seq=1, score_a=4
    )

    ov1 = client.get(f"/api/v1/matches/{match_id}/overlay")
    assert ov1.status_code == 200
    body1 = ov1.json()
    assert body1["version"] == 2
    assert body1["data"]["team_a"]["score"] == 4

    with client.websocket_connect(f"/ws/overlay/{match_id}") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "overlay.snapshot"
        assert snap["version"] == 2
        assert snap["data"]["team_a"]["score"] == 4

        _post_round_end(
            client, match_id=match_id, secret=secret, server_id=server_id, seq=2, score_a=5
        )
        pushed = ws.receive_json()
        assert pushed["type"] == "overlay.snapshot"
        assert pushed["version"] == 3
        assert pushed["data"]["team_a"]["score"] == 5

    # Reconnect → full snapshot again
    with client.websocket_connect(f"/ws/overlay/{match_id}") as ws2:
        again = ws2.receive_json()
        assert again["version"] == 3
        assert again["data"]["team_a"]["score"] == 5
