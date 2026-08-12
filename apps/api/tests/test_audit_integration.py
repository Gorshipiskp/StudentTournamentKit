"""Integration: GET /matches/{id}/audit — public list after start."""

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


def _login(client: TestClient) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "organizer", "password": "changeme_organizer"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_audit_404_and_lists_after_start(client: TestClient) -> None:
    assert client.get("/api/v1/matches/no_such_audit/audit").status_code == 404

    mid = f"m_aud_{uuid4().hex[:6]}"
    created = client.post(
        "/api/v1/matches",
        json={"match_id": mid, "game_server_id": "srv_fake", "map_name": "de_mirage"},
    )
    assert created.status_code == 200, created.text

    token = _login(client)
    headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": "int-audit-1"}
    start = client.post(f"/api/v1/matches/{mid}/start", headers=headers)
    assert start.status_code == 200, start.text

    # Director reads without bearer (TZ006 P6)
    got = client.get(f"/api/v1/matches/{mid}/audit")
    assert got.status_code == 200, got.text
    items = got.json()["items"]
    assert len(items) >= 1
    actions = {i["action"] for i in items}
    assert "organizer.match_start" in actions
    if len(items) >= 2:
        assert (items[0]["created_at"] or "") >= (items[1]["created_at"] or "")
