"""Integration: invites redeem/revoke/expired/wrong match + judge auth."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.token_hasher import hash_token
from app.main import app


def _configure_host_mysql() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3307")
    os.environ.setdefault("MYSQL_USER", "stk")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stk_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stk")
    os.environ.setdefault("STK_SESSION_SECRET", "dev_session_secret_change_me")
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


def _create_match(client: TestClient) -> str:
    match_id = f"m_inv_{uuid4().hex[:10]}"
    r = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": "srv_inv",
            "webhook_secret": "dev_webhook_secret_change_me",
            "map_name": "de_mirage",
        },
    )
    assert r.status_code == 200, r.text
    return match_id


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_redeem_and_judge_requires_session(client: TestClient) -> None:
    match_id = _create_match(client)

    bare = client.post(f"/api/v1/matches/{match_id}/judge/review-request")
    assert bare.status_code == 401

    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "judge"},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert "token" in body
    assert body["role"] == "judge"
    assert "judge.review" in body["caps"]

    redeemed = client.post("/api/v1/invites/redeem", json={"token": body["token"]})
    assert redeemed.status_code == 200, redeemed.text
    access = redeemed.json()["access_token"]
    assert set(redeemed.json()["caps"]) >= {"judge.review", "judge.resolve"}

    # Match not live → conflict, but auth passed (not 401/403)
    req = client.post(
        f"/api/v1/matches/{match_id}/judge/review-request",
        headers=_auth(access),
    )
    assert req.status_code in (200, 409), req.text


def test_revoke_blocks_redeem_and_session(client: TestClient) -> None:
    match_id = _create_match(client)
    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "judge"},
    ).json()
    invite_id = created["invite_id"]
    raw = created["token"]

    access = client.post("/api/v1/invites/redeem", json={"token": raw}).json()["access_token"]

    revoked = client.post("/api/v1/invites/revoke", json={"invite_id": invite_id})
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True

    bad = client.post("/api/v1/invites/redeem", json={"token": raw})
    assert bad.status_code == 403
    assert "revoked" in bad.json()["detail"].lower()

    # Already-issued session must also fail after revoke
    stale = client.post(
        f"/api/v1/matches/{match_id}/judge/review-request",
        headers=_auth(access),
    )
    assert stale.status_code == 401


def test_expired_invite(client: TestClient) -> None:
    match_id = _create_match(client)
    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "commentator", "ttl_seconds": 3600},
    )
    assert created.status_code == 200
    raw = created.json()["token"]
    invite_id = created.json()["invite_id"]

    # Force expire in DB
    with SqlAlchemyUnitOfWork() as uow:
        invite = uow.invites.get(invite_id)
        assert invite is not None
        invite.expires_at = datetime.now(UTC) - timedelta(seconds=5)
        uow.invites.save(invite)
        uow.commit()

    expired = client.post("/api/v1/invites/redeem", json={"token": raw})
    assert expired.status_code == 403
    assert "expired" in expired.json()["detail"].lower()


def test_wrong_match_forbidden(client: TestClient) -> None:
    match_a = _create_match(client)
    match_b = _create_match(client)
    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_a, "role": "judge"},
    ).json()
    access = client.post(
        "/api/v1/invites/redeem",
        json={"token": created["token"]},
    ).json()["access_token"]

    wrong = client.post(
        f"/api/v1/matches/{match_b}/judge/review-request",
        headers=_auth(access),
    )
    assert wrong.status_code == 403
    assert "not scoped" in wrong.json()["detail"].lower()


def test_commentator_cannot_call_judge(client: TestClient) -> None:
    match_id = _create_match(client)
    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "commentator"},
    ).json()
    access = client.post(
        "/api/v1/invites/redeem",
        json={"token": created["token"]},
    ).json()["access_token"]

    denied = client.post(
        f"/api/v1/matches/{match_id}/judge/review-request",
        headers=_auth(access),
    )
    assert denied.status_code == 403
    assert "capabilities" in denied.json()["detail"].lower()


def test_token_hash_not_raw(client: TestClient) -> None:
    match_id = _create_match(client)
    created = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "judge"},
    ).json()
    raw = created["token"]
    with SqlAlchemyUnitOfWork() as uow:
        invite = uow.invites.get(created["invite_id"])
        assert invite is not None
        assert invite.token_hash == hash_token(raw)
        assert invite.token_hash != raw
