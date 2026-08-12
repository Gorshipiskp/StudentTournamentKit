"""Integration: whip-publish / whep-play auth, TTL shape, max 2."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.infrastructure.realtime.whep_sessions import whep_sessions
from app.infrastructure.security.mediamtx_credentials import parse_mediamtx_bearer
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
    os.environ.setdefault("MEDIAMTX_PUBLIC_URL", "http://127.0.0.1:8889")
    os.environ.setdefault("MEDIAMTX_AUTH_SECRET", "dev_mediamtx_auth_secret_change_me")
    os.environ.setdefault("MEDIAMTX_CREDENTIAL_TTL_SECONDS", "600")
    os.environ["MYSQL_SSL"] = ""
    reset_engine_cache()
    reset_session_factory_cache()


@pytest.fixture(scope="module")
def mysql_ready() -> None:
    _configure()
    if not check_database():
        pytest.skip("MySQL not reachable (start infra/platform compose)")


@pytest.fixture
def client(mysql_ready: None) -> TestClient:
    whep_sessions.reset()
    return TestClient(app)


def _organizer(client: TestClient) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "organizer", "password": "changeme_organizer"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _match(client: TestClient) -> str:
    match_id = f"m_whip_{uuid4().hex[:10]}"
    r = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": "srv_whip",
            "webhook_secret": "dev_webhook_secret_change_me",
        },
    )
    assert r.status_code == 200, r.text
    return match_id


def _commentator(client: TestClient, match_id: str) -> str:
    inv = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "commentator"},
    )
    assert inv.status_code == 200, inv.text
    red = client.post("/api/v1/invites/redeem", json={"token": inv.json()["token"]})
    assert red.status_code == 200, red.text
    return red.json()["access_token"]


def test_whip_publish_organizer_only(client: TestClient) -> None:
    match_id = _match(client)
    denied = client.post(f"/api/v1/matches/{match_id}/whip-publish")
    assert denied.status_code == 401

    org = _organizer(client)
    ok = client.post(
        f"/api/v1/matches/{match_id}/whip-publish",
        headers={"Authorization": f"Bearer {org}"},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["path"] == f"stk/{match_id}"
    assert body["whip_url"].endswith(f"/stk/{match_id}/whip")
    assert body["ttl"] >= 60
    assert "bearer" in body and "jti" not in body
    claims = parse_mediamtx_bearer(body["bearer"])
    assert claims["act"] == "publish"
    assert claims["path"] == body["path"]

    missing = client.post(
        "/api/v1/matches/m_missing_xyz/whip-publish",
        headers={"Authorization": f"Bearer {org}"},
    )
    assert missing.status_code == 404


def test_whep_play_cap_and_auth(client: TestClient) -> None:
    match_id = _match(client)
    access_a = _commentator(client, match_id)
    access_b = _commentator(client, match_id)
    access_c = _commentator(client, match_id)

    # judge cannot
    inv = client.post(
        "/api/v1/invites", json={"match_id": match_id, "role": "judge"}
    ).json()
    judge = client.post(
        "/api/v1/invites/redeem", json={"token": inv["token"]}
    ).json()["access_token"]
    denied = client.post(
        f"/api/v1/matches/{match_id}/whep-play",
        headers={"Authorization": f"Bearer {judge}"},
    )
    assert denied.status_code == 403

    a = client.post(
        f"/api/v1/matches/{match_id}/whep-play",
        headers={"Authorization": f"Bearer {access_a}"},
    )
    # same invite refresh must not burn a second slot
    a_refresh = client.post(
        f"/api/v1/matches/{match_id}/whep-play",
        headers={"Authorization": f"Bearer {access_a}"},
    )
    b = client.post(
        f"/api/v1/matches/{match_id}/whep-play",
        headers={"Authorization": f"Bearer {access_b}"},
    )
    assert a.status_code == 200, a.text
    assert a_refresh.status_code == 200, a_refresh.text
    assert b.status_code == 200, b.text
    assert a.json()["whep_url"].endswith(f"/stk/{match_id}/whep")
    third = client.post(
        f"/api/v1/matches/{match_id}/whep-play",
        headers={"Authorization": f"Bearer {access_c}"},
    )
    assert third.status_code == 429, third.text


def test_mediamtx_auth_callback(client: TestClient) -> None:
    match_id = _match(client)
    org = _organizer(client)
    pub = client.post(
        f"/api/v1/matches/{match_id}/whip-publish",
        headers={"Authorization": f"Bearer {org}"},
    ).json()
    ok = client.post(
        "/api/v1/internal/mediamtx-auth",
        json={
            "user": "",
            "password": pub["bearer"],
            "action": "publish",
            "path": pub["path"],
            "protocol": "webrtc",
        },
    )
    assert ok.status_code == 200, ok.text

    bad = client.post(
        "/api/v1/internal/mediamtx-auth",
        json={
            "password": pub["bearer"],
            "action": "read",
            "path": pub["path"],
        },
    )
    assert bad.status_code == 403

    wrong_path = client.post(
        "/api/v1/internal/mediamtx-auth",
        json={
            "password": pub["bearer"],
            "action": "publish",
            "path": "stk/other",
        },
    )
    assert wrong_path.status_code == 403
