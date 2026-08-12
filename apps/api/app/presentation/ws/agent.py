"""WebSocket: Director Agent session (desired push / actual report)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.commands.update_production import (
    apply_agent_actual,
    get_production,
    set_agent_connection_status,
)
from app.domain.production.entities import AGENT_CONNECTED, AGENT_DISCONNECTED
from app.domain.production.messages import (
    TYPE_AGENT_HELLO,
    TYPE_AGENT_PING,
    TYPE_AGENT_PONG,
    TYPE_PRODUCTION_ACTUAL,
    TYPE_PRODUCTION_DESIRED,
    desired_message,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.agent_auth import verify_agent_token
from app.infrastructure.realtime.agent_hub import agent_hub

logger = logging.getLogger("stk.ws.agent")

router = APIRouter(tags=["agent-ws"])


def _extract_token(websocket: WebSocket) -> str | None:
    q = websocket.query_params.get("token")
    if q:
        return q
    return websocket.headers.get("x-stk-agent-token")


@router.websocket("/ws/agent/{match_id}")
async def ws_agent(websocket: WebSocket, match_id: str) -> None:
    if not verify_agent_token(_extract_token(websocket)):
        await websocket.close(code=4401)
        return

    with SqlAlchemyUnitOfWork() as uow:
        try:
            get_production(uow, match_id=match_id)
        except KeyError:
            await websocket.close(code=4404)
            return
        set_agent_connection_status(
            uow, match_id=match_id, agent_status=AGENT_CONNECTED
        )
        session = uow.production.get(match_id)
        assert session is not None
        initial = desired_message(session)
        uow.commit()

    queue = await agent_hub.connect(match_id, websocket)
    try:
        await websocket.send_json(initial)
        while True:
            get_task = asyncio.create_task(queue.get())
            recv_task = asyncio.create_task(websocket.receive_text())
            done, pending = await asyncio.wait(
                {get_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            if get_task in done:
                await websocket.send_json(get_task.result())
            if recv_task in done:
                raw = recv_task.result()
                await _handle_agent_inbound(match_id, raw, websocket)
    except WebSocketDisconnect:
        logger.info("agent_ws_disconnected match_id=%s", match_id)
    except asyncio.CancelledError:
        pass
    finally:
        await agent_hub.disconnect(match_id, websocket, queue)
        with SqlAlchemyUnitOfWork() as uow:
            set_agent_connection_status(
                uow, match_id=match_id, agent_status=AGENT_DISCONNECTED
            )
            uow.commit()


async def _handle_agent_inbound(
    match_id: str, raw: str, websocket: WebSocket
) -> None:
    try:
        body: Any = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_json({"type": "error", "detail": "invalid JSON"})
        return
    if not isinstance(body, dict):
        await websocket.send_json({"type": "error", "detail": "body must be object"})
        return

    msg_type = body.get("type")
    if msg_type == TYPE_AGENT_PING:
        await websocket.send_json({"protocol": 1, "type": TYPE_AGENT_PONG})
        return
    if msg_type == TYPE_AGENT_HELLO:
        # Desired is authoritative on reconnect (A12) — push current DB desired
        with SqlAlchemyUnitOfWork() as uow:
            session = uow.production.get(match_id)
            if session is not None:
                await websocket.send_json(desired_message(session))
        return
    if msg_type == TYPE_PRODUCTION_ACTUAL:
        actual = body.get("actual") if isinstance(body.get("actual"), dict) else {}
        try:
            with SqlAlchemyUnitOfWork() as uow:
                pub = apply_agent_actual(
                    uow,
                    match_id=match_id,
                    actual_scene=actual.get("scene")
                    if isinstance(actual.get("scene"), str)
                    else None,
                    actual_stream=actual.get("stream")
                    if isinstance(actual.get("stream"), str)
                    else None,
                    obs_status=body.get("obs_status")
                    if isinstance(body.get("obs_status"), str)
                    else None,
                    broadcast_status=body.get("broadcast_status")
                    if isinstance(body.get("broadcast_status"), str)
                    else None,
                    agent_status=AGENT_CONNECTED,
                )
                uow.commit()
        except Exception as exc:  # noqa: BLE001 — surface to agent
            await websocket.send_json({"type": "error", "detail": str(exc)})
            return
        await websocket.send_json(
            {
                "protocol": 1,
                "type": "production.actual_ack",
                "match_id": match_id,
                "actual": pub.get("actual"),
            }
        )
        return
