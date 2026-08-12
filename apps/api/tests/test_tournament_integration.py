"""Integration: organizer auth + tournament CRUD."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.main import app


def _configure_host_mysql() -> None:
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
    _configure_host_mysql()
    if not check_database():
        pytest.skip("MySQL not reachable (start infra/platform compose)")


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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_tournaments_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/tournaments").status_code == 401
    assert client.post("/api/v1/tournaments", json={"name": "x"}).status_code == 401


def test_login_bad_password(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "organizer", "password": "nope"},
    )
    assert r.status_code == 401


def test_login_create_list_publish(client: TestClient) -> None:
    token = _login(client)
    name = f"Cup {uuid4().hex[:6]}"

    created = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={
            "name": name,
            "format": "single_elim",
            "settings": {"configured_broadcast_delay_seconds": 20},
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["name"] == name
    assert body["status"] == "draft"
    tid = body["id"]

    listed = client.get("/api/v1/tournaments", headers=_auth(token))
    assert listed.status_code == 200
    ids = {i["id"] for i in listed.json()["items"]}
    assert tid in ids

    got = client.get(f"/api/v1/tournaments/{tid}", headers=_auth(token))
    assert got.status_code == 200
    assert got.json()["settings"]["configured_broadcast_delay_seconds"] == 20

    patched = client.patch(
        f"/api/v1/tournaments/{tid}",
        headers=_auth(token),
        json={"name": name + " v2"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == name + " v2"

    published = client.post(
        f"/api/v1/tournaments/{tid}/publish",
        headers=_auth(token),
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"


def test_fake_match_create_unaffected(client: TestClient) -> None:
    match_id = f"m_t5_{uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": "srv_t5",
            "webhook_secret": "dev_webhook_secret_change_me",
            "map_name": "de_mirage",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["id"] == match_id


def test_match_get_exposes_broadcast_delay_hint(client: TestClient) -> None:
    """Director reads configured_broadcast_delay_seconds from tournament (TZ006 P1)."""
    token = _login(client)
    created = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={
            "name": f"DelayCup {uuid4().hex[:6]}",
            "settings": {"configured_broadcast_delay_seconds": 105},
        },
    )
    assert created.status_code == 200, created.text
    tid = created.json()["id"]
    mid = f"m_delay_{uuid4().hex[:6]}"
    match = client.post(
        "/api/v1/matches",
        json={
            "match_id": mid,
            "tournament_id": tid,
            "game_server_id": "srv_delay",
            "map_name": "de_mirage",
        },
    )
    assert match.status_code == 200, match.text
    got = client.get(f"/api/v1/matches/{mid}")
    assert got.status_code == 200
    body = got.json()
    assert body["tournament_id"] == tid
    assert body["configured_broadcast_delay_seconds"] == 105
