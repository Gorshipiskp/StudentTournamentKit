"""Signaling message types (WebRTC P2P relay)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

PROTOCOL_VERSION = 1

TYPE_HELLO = "signaling.hello"
TYPE_PEER_JOINED = "signaling.peer_joined"
TYPE_PEER_LEFT = "signaling.peer_left"
TYPE_OFFER = "signaling.offer"
TYPE_ANSWER = "signaling.answer"
TYPE_ICE = "signaling.ice"
TYPE_ERROR = "error"

ROLE_PUBLISHER = "publisher"
ROLE_SUBSCRIBER = "subscriber"

RELAY_TYPES = frozenset({TYPE_OFFER, TYPE_ANSWER, TYPE_ICE})
MAX_SUBSCRIBERS = 2


def new_peer_id(role: str) -> str:
    prefix = "pub" if role == ROLE_PUBLISHER else "sub"
    return f"{prefix}_{uuid4().hex[:10]}"


def hello_message(*, role: str, peer_id: str, match_id: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_VERSION,
        "type": TYPE_HELLO,
        "role": role,
        "peer_id": peer_id,
        "match_id": match_id,
    }


def peer_joined_message(*, peer_id: str, role: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_VERSION,
        "type": TYPE_PEER_JOINED,
        "peer_id": peer_id,
        "role": role,
    }


def peer_left_message(*, peer_id: str) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_VERSION,
        "type": TYPE_PEER_LEFT,
        "peer_id": peer_id,
    }


def error_message(detail: str) -> dict[str, Any]:
    return {"protocol": PROTOCOL_VERSION, "type": TYPE_ERROR, "detail": detail}
