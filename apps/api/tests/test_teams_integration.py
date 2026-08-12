"""Integration: teams scoped by tournament."""

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


def _create_tournament(client: TestClient, token: str, name: str) -> str:
    r = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={"name": name, "format": "single_elim", "settings": {}},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_teams_require_auth(client: TestClient) -> None:
    assert client.get(f"/api/v1/tournaments/{uuid4()}/teams").status_code == 401


def test_four_teams_isolated_across_tournaments(client: TestClient) -> None:
    token = _login(client)
    suffix = uuid4().hex[:6]
    t1 = _create_tournament(client, token, f"T1-{suffix}")
    t2 = _create_tournament(client, token, f"T2-{suffix}")

    for i in range(4):
        r = client.post(
            f"/api/v1/tournaments/{t1}/teams",
            headers=_auth(token),
            json={"name": f"A{i}-{suffix}", "tag": f"A{i}"},
        )
        assert r.status_code == 200, r.text
        team_id = r.json()["id"]
        pr = client.post(
            f"/api/v1/tournaments/{t1}/teams/{team_id}/players",
            headers=_auth(token),
            json={"nickname": f"player{i}"},
        )
        assert pr.status_code == 200, pr.text

    # duplicate name rejected
    dup = client.post(
        f"/api/v1/tournaments/{t1}/teams",
        headers=_auth(token),
        json={"name": f"A0-{suffix}"},
    )
    assert dup.status_code == 400

    # same name ok on other tournament
    ok = client.post(
        f"/api/v1/tournaments/{t2}/teams",
        headers=_auth(token),
        json={"name": f"A0-{suffix}"},
    )
    assert ok.status_code == 200, ok.text

    listed1 = client.get(f"/api/v1/tournaments/{t1}/teams", headers=_auth(token))
    listed2 = client.get(f"/api/v1/tournaments/{t2}/teams", headers=_auth(token))
    assert listed1.status_code == 200
    assert listed2.status_code == 200
    assert len(listed1.json()["items"]) == 4
    assert len(listed2.json()["items"]) == 1
    assert all(len(t["players"]) == 1 for t in listed1.json()["items"])
