"""Integration: bracket generate + assign + match link."""

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


def test_bracket_generate_assign_links_matches(client: TestClient) -> None:
    token = _login(client)
    suffix = uuid4().hex[:6]
    t = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={"name": f"Br-{suffix}", "format": "single_elim", "settings": {}},
    )
    assert t.status_code == 200, t.text
    tid = t.json()["id"]

    team_ids = []
    for i in range(4):
        r = client.post(
            f"/api/v1/tournaments/{tid}/teams",
            headers=_auth(token),
            json={"name": f"B{i}-{suffix}"},
        )
        assert r.status_code == 200, r.text
        team_ids.append(r.json()["id"])

    gen = client.post(
        f"/api/v1/tournaments/{tid}/bracket/generate?size=4",
        headers=_auth(token),
        json={"size": 4},
    )
    assert gen.status_code == 200, gen.text
    items = gen.json()["items"]
    assert len(items) == 3
    sf = [n for n in items if n["round"] == 0]
    final = [n for n in items if n["round"] == 1][0]
    assert len(sf) == 2

    for node, a, b in ((sf[0], 0, 1), (sf[1], 2, 3)):
        p = client.patch(
            f"/api/v1/tournaments/{tid}/bracket/nodes/{node['id']}",
            headers=_auth(token),
            json={"team_a_id": team_ids[a], "team_b_id": team_ids[b]},
        )
        assert p.status_code == 200, p.text
        assert p.json()["match_id"]

    fin = client.patch(
        f"/api/v1/tournaments/{tid}/bracket/nodes/{final['id']}",
        headers=_auth(token),
        json={"team_a_id": team_ids[0], "team_b_id": team_ids[2]},
    )
    assert fin.status_code == 200, fin.text
    assert fin.json()["match_id"]

    tree = client.get(f"/api/v1/tournaments/{tid}/bracket", headers=_auth(token))
    assert tree.status_code == 200
    linked = [n for n in tree.json()["items"] if n["match_id"]]
    assert len(linked) == 3
