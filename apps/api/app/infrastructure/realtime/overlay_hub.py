"""In-memory overlay WS hub (single replica, A9)."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger("stk.overlay_hub")


class OverlayHub:
    """Fan-out full overlay.snapshot messages per match_id."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(self, match_id: str, websocket: WebSocket) -> asyncio.Queue[dict[str, Any]]:
        await websocket.accept()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._rooms[match_id].add(websocket)
            self._queues[match_id].append(queue)
        return queue

    async def disconnect(self, match_id: str, websocket: WebSocket, queue: asyncio.Queue[dict[str, Any]]) -> None:
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
        """Sync-safe publish from outbox dispatcher (same process)."""
        queues = list(self._queues.get(match_id, []))
        delivered = 0
        for queue in queues:
            try:
                queue.put_nowait(message)
                delivered += 1
            except Exception:
                logger.exception("overlay_hub_publish_failed match_id=%s", match_id)
        logger.info(
            "overlay_hub_publish match_id=%s version=%s subscribers=%s",
            match_id,
            message.get("version"),
            delivered,
        )
        return delivered

    def subscriber_count(self, match_id: str) -> int:
        return len(self._queues.get(match_id, []))


overlay_hub = OverlayHub()
