"""Integration: two peers exchange signaling; TURN credentials + auth."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import reset_session_factory_cache
from app.infrastructure.realtime.agent_auth import DEFAULT_DEV_TOKEN
from app.infrastructure.realtime.signaling_hub import signaling_hub
from app.infrastructure.security.turn_credentials import credentials_expired
from app.main import app


def _configure_host_mysql() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3307")
    os.environ.setdefault("MYSQL_USER", "stk")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stk_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stk")
    os.environ.setdefault("STK_SESSION_SECRET", "dev_session_secret_change_me")
    os.environ.setdefault("STK_AGENT_TOKEN", DEFAULT_DEV_TOKEN)
    os.environ.setdefault("TURN_SECRET", "dev_turn_secret_change_me")
    os.environ.setdefault("TURN_HOST", "127.0.0.1")
    os.environ["MYSQL_SSL"] = ""
    reset_engine_cache()
    reset_session_factory_cache()


@pytest.fixture(scope="module")
def mysql_ready() -> None:
    _configure_host_mysql()
    if not check_database():
        pytest.skip("MySQL not reachable (start infra/platform compose)")


@pytest.fixture
def client(mysql_ready: None) -> TestClient:
    signaling_hub.reset()
    return TestClient(app)


def _match(client: TestClient) -> str:
    match_id = f"m_sig_{uuid4().hex[:10]}"
    r = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "game_server_id": "srv_sig",
            "webhook_secret": "dev_webhook_secret_change_me",
        },
    )
    assert r.status_code == 200, r.text
    return match_id


def _commentator_access(client: TestClient, match_id: str) -> str:
    inv = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "commentator"},
    )
    assert inv.status_code == 200, inv.text
    red = client.post("/api/v1/invites/redeem", json={"token": inv.json()["token"]})
    assert red.status_code == 200, red.text
    return red.json()["access_token"]


def test_signaling_offer_answer_between_peers(client: TestClient) -> None:
    match_id = _match(client)
    access = _commentator_access(client, match_id)

    with client.websocket_connect(
        f"/ws/signaling/{match_id}?role=publisher&token={DEFAULT_DEV_TOKEN}"
    ) as pub:
        hello_pub = pub.receive_json()
        assert hello_pub["type"] == "signaling.hello"
        assert hello_pub["role"] == "publisher"
        pub_id = hello_pub["peer_id"]

        with client.websocket_connect(
            f"/ws/signaling/{match_id}?role=subscriber&token={access}"
        ) as sub:
            hello_sub = sub.receive_json()
            assert hello_sub["type"] == "signaling.hello"
            sub_id = hello_sub["peer_id"]

            joined = pub.receive_json()
            assert joined["type"] == "signaling.peer_joined"
            assert joined["peer_id"] == sub_id

            pub.send_json(
                {
                    "protocol": 1,
                    "type": "signaling.offer",
                    "from": pub_id,
                    "to": sub_id,
                    "sdp": "fake-offer-sdp",
                }
            )
            offer = sub.receive_json()
            assert offer["type"] == "signaling.offer"
            assert offer["sdp"] == "fake-offer-sdp"

            sub.send_json(
                {
                    "protocol": 1,
                    "type": "signaling.answer",
                    "from": sub_id,
                    "to": pub_id,
                    "sdp": "fake-answer-sdp",
                }
            )
            answer = pub.receive_json()
            assert answer["type"] == "signaling.answer"
            assert answer["sdp"] == "fake-answer-sdp"

            pub.send_json(
                {
                    "protocol": 1,
                    "type": "signaling.ice",
                    "from": pub_id,
                    "to": sub_id,
                    "candidate": {"candidate": "candidate:1", "sdpMid": "0"},
                }
            )
            ice = sub.receive_json()
            assert ice["type"] == "signaling.ice"


def test_signaling_rejects_bad_auth(client: TestClient) -> None:
    match_id = _match(client)
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/ws/signaling/{match_id}?role=subscriber&token=bad"
        ):
            pass


def test_turn_credentials_agent_and_expiry(client: TestClient) -> None:
    match_id = _match(client)
    r = client.post(
        f"/api/v1/matches/{match_id}/turn-credentials",
        headers={"X-STK-Agent-Token": DEFAULT_DEV_TOKEN},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ttl"] >= 30
    assert body["username"]
    assert body["credential"]
    assert any(u.startswith("turn:") for u in body["urls"])
    assert not credentials_expired(body["username"])

    # Judge session cannot get TURN
    inv = client.post(
        "/api/v1/invites",
        json={"match_id": match_id, "role": "judge"},
    ).json()
    judge = client.post(
        "/api/v1/invites/redeem", json={"token": inv["token"]}
    ).json()["access_token"]
    denied = client.post(
        f"/api/v1/matches/{match_id}/turn-credentials",
        headers={"Authorization": f"Bearer {judge}"},
    )
    assert denied.status_code == 403

    # Commentator OK
    access = _commentator_access(client, match_id)
    ok = client.post(
        f"/api/v1/matches/{match_id}/turn-credentials",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert ok.status_code == 200, ok.text
