"""Integration: GET /matches/{id}/health — 404 + Fake OBS shape."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.main import app


def _configure() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3307")
    os.environ.setdefault("MYSQL_USER", "stk")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stk_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stk")
    os.environ.setdefault("STK_SESSION_SECRET", "dev_session_secret_change_me")
    os.environ.setdefault("STK_ORGANIZER_USERNAME", "organizer")
    os.environ.setdefault("STK_ORGANIZER_PASSWORD", "changeme_organizer")
    reset_engine_cache()
    reset_session_factory_cache()


@pytest.fixture(scope="module")
def mysql_ready() -> None:
    _configure()
    if not check_database():
        pytest.skip("MySQL not reachable")


@pytest.fixture
def client(mysql_ready: None) -> TestClient:
    return TestClient(app)


def test_health_404_and_public_ok(client: TestClient) -> None:
    assert client.get("/api/v1/matches/no_such_match/health").status_code == 404

    mid = f"m_hlth_{uuid4().hex[:6]}"
    created = client.post(
        "/api/v1/matches",
        json={"match_id": mid, "game_server_id": "srv_fake", "map_name": "de_mirage"},
    )
    assert created.status_code == 200, created.text

    # public (director) — no bearer
    got = client.get(f"/api/v1/matches/{mid}/health")
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["match_id"] == mid
    assert "overall" in body
    assert set(body["components"]) >= {
        "platform",
        "agent",
        "obs",
        "overlay",
        "game_server",
        "broadcast",
    }
    assert body["components"]["game_server"]["mode"] == "fake"
