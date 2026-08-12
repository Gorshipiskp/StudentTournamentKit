"""WebSocket: overlay full snapshot channel."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.commands.rebuild_overlay import get_overlay_message
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.overlay_hub import overlay_hub

logger = logging.getLogger("stk.ws.overlay")

router = APIRouter(tags=["overlay-ws"])


@router.websocket("/ws/overlay/{match_id}")
async def ws_overlay(websocket: WebSocket, match_id: str) -> None:
    with SqlAlchemyUnitOfWork() as uow:
        message = get_overlay_message(uow, match_id)
        if message is None:
            await websocket.close(code=4404)
            return
        uow.commit()

    queue = await overlay_hub.connect(match_id, websocket)
    try:
        await websocket.send_json(message)
        while True:
            try:
                # Wait for hub push or client disconnect (receive)
                get_task = asyncio.create_task(queue.get())
                recv_task = asyncio.create_task(websocket.receive_text())
                done, pending = await asyncio.wait(
                    {get_task, recv_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                if get_task in done:
                    payload = get_task.result()
                    await websocket.send_json(payload)
                if recv_task in done:
                    # Client ping/text ignored; disconnect raises below
                    _ = recv_task.result()
            except WebSocketDisconnect:
                break
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.info("overlay_ws_disconnected match_id=%s", match_id)
    finally:
        await overlay_hub.disconnect(match_id, websocket, queue)
