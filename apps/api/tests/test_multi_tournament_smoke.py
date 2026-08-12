"""Smoke: two published tournaments in parallel — isolated teams/matches/invites."""

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


def _publish_cup(client: TestClient, token: str, name: str) -> str:
    created = client.post(
        "/api/v1/tournaments",
        headers=_auth(token),
        json={"name": name, "format": "single_elim", "settings": {}},
    )
    assert created.status_code == 200, created.text
    tid = created.json()["id"]
    pub = client.post(f"/api/v1/tournaments/{tid}/publish", headers=_auth(token))
    assert pub.status_code == 200, pub.text
    assert pub.json()["status"] == "published"
    return tid


def _seed_bracket(client: TestClient, token: str, tid: str) -> list[str]:
    """4 teams + size-4 bracket; fill round-0; return match_ids."""
    team_ids: list[str] = []
    for i in range(4):
        # Same display names across tournaments must not collide.
        r = client.post(
            f"/api/v1/tournaments/{tid}/teams",
            headers=_auth(token),
            json={"name": f"Alpha{i}"},
        )
        assert r.status_code == 200, r.text
        team_ids.append(r.json()["id"])

    gen = client.post(
        f"/api/v1/tournaments/{tid}/bracket/generate?size=4",
        headers=_auth(token),
        json={"size": 4},
    )
    assert gen.status_code == 200, gen.text
    sf = [n for n in gen.json()["items"] if n["round"] == 0]
    assert len(sf) == 2

    match_ids: list[str] = []
    for node, a, b in ((sf[0], 0, 1), (sf[1], 2, 3)):
        p = client.patch(
            f"/api/v1/tournaments/{tid}/bracket/nodes/{node['id']}",
            headers=_auth(token),
            json={"team_a_id": team_ids[a], "team_b_id": team_ids[b]},
        )
        assert p.status_code == 200, p.text
        mid = p.json()["match_id"]
        assert mid
        match_ids.append(mid)

    # Sanity: team list stays scoped to this tournament
    teams = client.get(f"/api/v1/tournaments/{tid}/teams", headers=_auth(token))
    assert teams.status_code == 200
    assert {t["id"] for t in teams.json()["items"]} == set(team_ids)
    assert all(t["name"].startswith("Alpha") for t in teams.json()["items"])
    return match_ids


def test_two_published_tournaments_isolated(client: TestClient) -> None:
    token = _login(client)
    s1 = uuid4().hex[:6]
    s2 = uuid4().hex[:6]

    tid_a = _publish_cup(client, token, f"CupA-{s1}")
    tid_b = _publish_cup(client, token, f"CupB-{s2}")
    assert tid_a != tid_b

    matches_a = _seed_bracket(client, token, tid_a)
    matches_b = _seed_bracket(client, token, tid_b)
    assert set(matches_a).isdisjoint(set(matches_b))

    # Teams of A must not appear under B
    teams_a = {
        t["id"]
        for t in client.get(f"/api/v1/tournaments/{tid_a}/teams", headers=_auth(token)).json()[
            "items"
        ]
    }
    teams_b = {
        t["id"]
        for t in client.get(f"/api/v1/tournaments/{tid_b}/teams", headers=_auth(token)).json()[
            "items"
        ]
    }
    assert teams_a.isdisjoint(teams_b)

    # Start + staff links on one match each — invites bind to that match only
    mid_a, mid_b = matches_a[0], matches_b[0]
    for mid in (mid_a, mid_b):
        st = client.post(f"/api/v1/matches/{mid}/start", headers=_auth(token))
        assert st.status_code == 200, st.text
        assert st.json()["match"]["status"] == "live"

    links_a = client.post(f"/api/v1/matches/{mid_a}/staff-links", headers=_auth(token))
    links_b = client.post(f"/api/v1/matches/{mid_b}/staff-links", headers=_auth(token))
    assert links_a.status_code == 200, links_a.text
    assert links_b.status_code == 200, links_b.text

    ja = links_a.json()["judge"]["token"]
    jb = links_b.json()["judge"]["token"]
    assert ja != jb

    ra = client.post("/api/v1/invites/redeem", json={"token": ja})
    rb = client.post("/api/v1/invites/redeem", json={"token": jb})
    assert ra.status_code == 200, ra.text
    assert rb.status_code == 200, rb.text
    assert ra.json()["match_id"] == mid_a
    assert rb.json()["match_id"] == mid_b
    assert ra.json()["access_token"] != rb.json()["access_token"]
