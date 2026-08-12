"""In-memory WebRTC signaling relay hub (single replica, A9 / F6)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from starlette.websockets import WebSocket

from app.domain.signaling.messages import (
    MAX_SUBSCRIBERS,
    ROLE_PUBLISHER,
    ROLE_SUBSCRIBER,
    TYPE_ANSWER,
    TYPE_ICE,
    TYPE_OFFER,
    peer_joined_message,
    peer_left_message,
)

logger = logging.getLogger("stk.signaling_hub")


@dataclass
class SignalingPeer:
    peer_id: str
    role: str
    websocket: WebSocket
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)


class SignalingHub:
    """Match-scoped publisher/subscriber rooms; relay offer/answer/ICE by peer_id."""

    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, SignalingPeer]] = {}
        self._lock = asyncio.Lock()

    async def try_register(
        self,
        match_id: str,
        *,
        peer_id: str,
        role: str,
        websocket: WebSocket,
    ) -> tuple[SignalingPeer | None, str | None]:
        """Accept socket and register. Returns (peer, error_code) — error_code e.g. 'full'."""
        await websocket.accept()
        async with self._lock:
            room = self._rooms.setdefault(match_id, {})
            if role == ROLE_SUBSCRIBER:
                subs = [p for p in room.values() if p.role == ROLE_SUBSCRIBER]
                if len(subs) >= MAX_SUBSCRIBERS:
                    return None, "full"
            if role == ROLE_PUBLISHER:
                pubs = [p for p in room.values() if p.role == ROLE_PUBLISHER]
                if pubs:
                    return None, "publisher_exists"
            peer = SignalingPeer(peer_id=peer_id, role=role, websocket=websocket)
            room[peer_id] = peer
            return peer, None

    async def unregister(self, match_id: str, peer_id: str) -> None:
        left: SignalingPeer | None = None
        notify: list[SignalingPeer] = []
        async with self._lock:
            room = self._rooms.get(match_id)
            if not room:
                return
            left = room.pop(peer_id, None)
            if not room:
                self._rooms.pop(match_id, None)
            elif left is not None:
                notify = list(room.values())
        if left is not None:
            msg = peer_left_message(peer_id=peer_id)
            for peer in notify:
                self._enqueue(peer, msg)

    def publish_peer_joined(self, match_id: str, joined: SignalingPeer) -> int:
        """Notify publishers when a subscriber joins (so they can offer)."""
        if joined.role != ROLE_SUBSCRIBER:
            return 0
        room = self._rooms.get(match_id, {})
        msg = peer_joined_message(peer_id=joined.peer_id, role=joined.role)
        delivered = 0
        for peer in room.values():
            if peer.role == ROLE_PUBLISHER and peer.peer_id != joined.peer_id:
                self._enqueue(peer, msg)
                delivered += 1
        return delivered

    def list_subscribers(self, match_id: str) -> list[str]:
        room = self._rooms.get(match_id, {})
        return [p.peer_id for p in room.values() if p.role == ROLE_SUBSCRIBER]

    def list_publishers(self, match_id: str) -> list[str]:
        room = self._rooms.get(match_id, {})
        return [p.peer_id for p in room.values() if p.role == ROLE_PUBLISHER]

    def relay(
        self,
        match_id: str,
        *,
        sender_id: str,
        message: dict[str, Any],
    ) -> str | None:
        """
        Relay offer/answer/ice. Returns None on success, else error detail.
        """
        msg_type = message.get("type")
        if msg_type not in {TYPE_OFFER, TYPE_ANSWER, TYPE_ICE}:
            return f"unsupported type: {msg_type}"
        to_id = message.get("to")
        from_id = message.get("from")
        if not isinstance(to_id, str) or not isinstance(from_id, str):
            return "from/to required"
        if from_id != sender_id:
            return "from must match sender peer_id"
        room = self._rooms.get(match_id, {})
        sender = room.get(sender_id)
        target = room.get(to_id)
        if sender is None:
            return "sender not registered"
        if target is None:
            return "target peer not connected"
        # Role sanity: offer publisher→subscriber; answer subscriber→publisher; ice either way
        if msg_type == TYPE_OFFER and sender.role != ROLE_PUBLISHER:
            return "only publisher may send offer"
        if msg_type == TYPE_ANSWER and sender.role != ROLE_SUBSCRIBER:
            return "only subscriber may send answer"
        payload = dict(message)
        payload.setdefault("protocol", 1)
        self._enqueue(target, payload)
        logger.info(
            "signaling_relay match_id=%s type=%s from=%s to=%s",
            match_id,
            msg_type,
            sender_id,
            to_id,
        )
        return None

    def _enqueue(self, peer: SignalingPeer, message: dict[str, Any]) -> None:
        try:
            peer.queue.put_nowait(message)
        except Exception:
            logger.exception("signaling_enqueue_failed peer_id=%s", peer.peer_id)

    def reset(self) -> None:
        """Test helper."""
        self._rooms.clear()


signaling_hub = SignalingHub()
