"""Unit: signaling hub relay + TURN credential TTL."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from app.domain.signaling.messages import (
    ROLE_PUBLISHER,
    ROLE_SUBSCRIBER,
    TYPE_ANSWER,
    TYPE_OFFER,
)
from app.infrastructure.realtime.signaling_hub import SignalingHub
from app.infrastructure.security.turn_credentials import (
    credentials_expired,
    issue_turn_credentials,
)


def test_hub_relays_offer_and_answer() -> None:
    async def _run() -> None:
        hub = SignalingHub()
        pub_ws = MagicMock()
        sub_ws = MagicMock()

        async def _accept(*_a, **_k):
            return None

        pub_ws.accept = _accept
        sub_ws.accept = _accept

        pub, err = await hub.try_register(
            "m1", peer_id="pub_1", role=ROLE_PUBLISHER, websocket=pub_ws
        )
        assert err is None and pub is not None
        sub, err = await hub.try_register(
            "m1", peer_id="sub_1", role=ROLE_SUBSCRIBER, websocket=sub_ws
        )
        assert err is None and sub is not None
        assert hub.publish_peer_joined("m1", sub) == 1
        joined = await asyncio.wait_for(pub.queue.get(), timeout=1)
        assert joined["type"] == "signaling.peer_joined"
        assert joined["peer_id"] == "sub_1"

        err = hub.relay(
            "m1",
            sender_id="pub_1",
            message={
                "type": TYPE_OFFER,
                "from": "pub_1",
                "to": "sub_1",
                "sdp": "v=0 offer",
            },
        )
        assert err is None
        got = await asyncio.wait_for(sub.queue.get(), timeout=1)
        assert got["type"] == TYPE_OFFER
        assert got["sdp"] == "v=0 offer"

        err = hub.relay(
            "m1",
            sender_id="sub_1",
            message={
                "type": TYPE_ANSWER,
                "from": "sub_1",
                "to": "pub_1",
                "sdp": "v=0 answer",
            },
        )
        assert err is None
        got = await asyncio.wait_for(pub.queue.get(), timeout=1)
        assert got["type"] == TYPE_ANSWER

        err = hub.relay(
            "m1",
            sender_id="sub_1",
            message={"type": TYPE_OFFER, "from": "sub_1", "to": "pub_1", "sdp": "x"},
        )
        assert err is not None

    asyncio.run(_run())


def test_hub_max_two_subscribers() -> None:
    async def _run() -> None:
        hub = SignalingHub()

        async def _accept(*_a, **_k):
            return None

        for i in range(2):
            ws = MagicMock()
            ws.accept = _accept
            peer, err = await hub.try_register(
                "m2", peer_id=f"sub_{i}", role=ROLE_SUBSCRIBER, websocket=ws
            )
            assert err is None and peer is not None
        ws3 = MagicMock()
        ws3.accept = _accept
        peer, err = await hub.try_register(
            "m2", peer_id="sub_2", role=ROLE_SUBSCRIBER, websocket=ws3
        )
        assert peer is None and err == "full"

    asyncio.run(_run())


def test_turn_credentials_issue_and_expire() -> None:
    creds = issue_turn_credentials(
        match_id="m_turn",
        now=1_700_000_000.0,
        ttl=300,
        secret="test_secret",
        host="turn.example",
        port=3478,
    )
    assert creds["ttl"] == 300
    assert creds["username"].startswith("1700000300:")
    assert "turn:turn.example:3478?transport=udp" in creds["urls"]
    assert not credentials_expired(creds["username"], now=1_700_000_100.0)
    assert credentials_expired(creds["username"], now=1_700_000_301.0)
