"""Integration: Fake-shaped webhook → GET match score (MySQL)."""

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
    os.environ.setdefault("MYSQL_USER", "stp")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stp_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stp")
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


def test_ingest_score_visible_on_get_and_duplicate_noop(client: TestClient) -> None:
    secret = "dev_webhook_secret_change_me"
    match_id = f"m_{uuid4().hex[:12]}"
    server_id = "srv_fake"

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
    assert created.json()["id"] == match_id

    event = {
        "event_id": str(uuid4()),
        "sequence": 1,
        "server_id": server_id,
        "match_id": match_id,
        "type": "round_end",
        "timestamp": "2026-08-11T18:00:00Z",
        "correlation_id": "itest",
        "payload": {
            "round": 1,
            "score": {"team_a": 3, "team_b": 1},
            "map": "de_mirage",
        },
    }
    raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-STP-Signature": sign_body(secret, raw),
        "X-STP-Event-Id": event["event_id"],
    }

    r1 = client.post("/api/v1/internal/cs2/events", content=raw, headers=headers)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert body1["applied"] is True
    assert body1["match"]["score"]["team_a"] == 3

    got = client.get(f"/api/v1/matches/{match_id}")
    assert got.status_code == 200
    assert got.json()["score"] == {"team_a": 3, "team_b": 1}
    assert got.json()["status"] == "live"
    assert got.json()["last_sequence"] == 1

    # Duplicate event_id — same body/signature
    r2 = client.post("/api/v1/internal/cs2/events", content=raw, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
    assert r2.json()["applied"] is False

    got2 = client.get(f"/api/v1/matches/{match_id}")
    assert got2.json()["score"]["team_a"] == 3

    # Bad HMAC
    bad = client.post(
        "/api/v1/internal/cs2/events",
        content=raw,
        headers={**headers, "X-STP-Signature": "sha256=deadbeef"},
    )
    assert bad.status_code == 401
