"""Integration: PUT branding → overlay snapshot branding fields."""

from __future__ import annotations

import io
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.main import app

_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


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


def test_branding_upload_overlay_and_public_logo(client: TestClient) -> None:
    token = _login(client)
    suffix = uuid4().hex[:6]
    t = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={"name": f"Branding-{suffix}", "format": "single_elim", "settings": {}},
    )
    assert t.status_code == 200, t.text
    tid = t.json()["id"]

    mid = f"m_br_{suffix}"
    m = client.post(
        "/api/v1/matches",
        json={
            "match_id": mid,
            "tournament_id": tid,
            "game_server_id": "srv_br",
            "webhook_secret": "dev_webhook_secret_change_me",
            "map_name": "de_mirage",
        },
    )
    assert m.status_code == 200, m.text

    put = client.put(
        f"/api/v1/tournaments/{tid}/branding",
        headers=_auth(token),
        data={"colors": '{"primary":"#112233","accent":"#aabbcc"}'},
        files={"logo": ("logo.png", io.BytesIO(_TINY_PNG), "image/png")},
    )
    assert put.status_code == 200, put.text
    assert put.json()["has_logo"] is True

    ov = client.get(f"/api/v1/matches/{mid}/overlay")
    assert ov.status_code == 200, ov.text
    branding = ov.json()["data"]["branding"]
    assert branding["logo_url"] == f"/api/v1/tournaments/{tid}/branding/logo"
    assert branding["colors"]["primary"] == "#112233"
    assert ov.json()["data"]["watermark"]["visible"] is True

    logo = client.get(f"/api/v1/tournaments/{tid}/branding/logo")
    assert logo.status_code == 200
    assert logo.content[:8] == b"\x89PNG\r\n\x1a\n"

    huge = client.put(
        f"/api/v1/tournaments/{tid}/branding",
        headers=_auth(token),
        files={
            "logo": (
                "big.png",
                io.BytesIO(b"x" * (2 * 1024 * 1024 + 10)),
                "image/png",
            )
        },
    )
    assert huge.status_code == 400
