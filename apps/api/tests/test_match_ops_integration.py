"""Integration: organizer start + staff-links; judge redeem still works."""

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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_start_and_staff_links_require_auth(client: TestClient) -> None:
    mid = f"m_ops_{uuid4().hex[:6]}"
    client.post(
        "/api/v1/matches",
        json={"match_id": mid, "game_server_id": "srv", "map_name": "de_mirage"},
    )
    assert client.post(f"/api/v1/matches/{mid}/start").status_code == 401
    assert client.post(f"/api/v1/matches/{mid}/staff-links").status_code == 401


def test_organizer_start_and_judge_redeem(client: TestClient) -> None:
    token = _login(client)
    mid = f"m_ops_{uuid4().hex[:6]}"
    created = client.post(
        "/api/v1/matches",
        json={
            "match_id": mid,
            "game_server_id": "srv_fake",
            "webhook_secret": "dev_webhook_secret_change_me",
            "map_name": "de_mirage",
        },
    )
    assert created.status_code == 200, created.text

    start = client.post(f"/api/v1/matches/{mid}/start", headers=_auth(token))
    assert start.status_code == 200, start.text
    assert start.json()["match"]["status"] == "live"
    assert start.json()["mode"] == "fake"

    links = client.post(f"/api/v1/matches/{mid}/staff-links", headers=_auth(token))
    assert links.status_code == 200, links.text
    body = links.json()
    assert body["director_url"].endswith(f"/director/{mid}")
    judge_token = body["judge"]["token"]

    redeemed = client.post("/api/v1/invites/redeem", json={"token": judge_token})
    assert redeemed.status_code == 200, redeemed.text
    assert redeemed.json()["role"] == "judge"
    access = redeemed.json()["access_token"]

    # live match — review request should auth-pass (200 or 409 depending on round)
    req = client.post(
        f"/api/v1/matches/{mid}/judge/review-request",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert req.status_code in (200, 409), req.text
