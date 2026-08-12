"""In-memory Director Agent WS hub (single replica, A9)."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger("stk.agent_hub")


class AgentHub:
    """Fan-out production.desired (and related) to Agent sessions per match."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(
        self, match_id: str, websocket: WebSocket
    ) -> asyncio.Queue[dict[str, Any]]:
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._rooms[match_id].add(websocket)
            self._queues[match_id].append(queue)
        return queue

    async def disconnect(
        self,
        match_id: str,
        websocket: WebSocket,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        async with self._lock:
            self._rooms[match_id].discard(websocket)
            queues = self._queues.get(match_id, [])
            if queue in queues:
                queues.remove(queue)
            if not self._rooms[match_id]:
                self._rooms.pop(match_id, None)
            if not self._queues.get(match_id):
                self._queues.pop(match_id, None)

    def publish(self, match_id: str, message: dict[str, Any]) -> int:
        queues = list(self._queues.get(match_id, []))
        delivered = 0
        for queue in queues:
            try:
                queue.put_nowait(message)
                delivered += 1
            except Exception:
                logger.exception("agent_hub_publish_failed match_id=%s", match_id)
        logger.info(
            "agent_hub_publish match_id=%s type=%s subscribers=%s",
            match_id,
            message.get("type"),
            delivered,
        )
        return delivered

    def subscriber_count(self, match_id: str) -> int:
        return len(self._queues.get(match_id, []))


agent_hub = AgentHub()
