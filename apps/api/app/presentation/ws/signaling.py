"""WebSocket: WebRTC signaling relay (publisher Agent ↔ subscriber commentator)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.identity.caps import CAP_COMMENTATOR_WATCH
from app.domain.signaling.messages import (
    RELAY_TYPES,
    ROLE_PUBLISHER,
    ROLE_SUBSCRIBER,
    error_message,
    hello_message,
    new_peer_id,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.agent_auth import verify_agent_token
from app.infrastructure.realtime.signaling_hub import signaling_hub
from app.infrastructure.security.session_token import parse_session_token

logger = logging.getLogger("stk.ws.signaling")

router = APIRouter(tags=["signaling-ws"])


def _extract_token(websocket: WebSocket) -> str | None:
    q = websocket.query_params.get("token") or websocket.query_params.get("access_token")
    if q:
        return q
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return websocket.headers.get("x-stk-agent-token")


def _authorize(websocket: WebSocket, match_id: str, role: str) -> str | None:
    """Return close reason or None if OK."""
    token = _extract_token(websocket)
    if role == ROLE_PUBLISHER:
        if not verify_agent_token(token):
            return "unauthorized publisher"
        return None
    if role == ROLE_SUBSCRIBER:
        if not token:
            return "missing subscriber token"
        try:
            session = parse_session_token(token)
        except ValueError:
            return "invalid session"
        if not session.requires_match(match_id):
            return "session not scoped to this match"
        if not session.has_cap(CAP_COMMENTATOR_WATCH):
            return "missing commentator.watch"
        with SqlAlchemyUnitOfWork() as uow:
            invite = uow.invites.get(session.invite_id)
            if invite is None or invite.is_revoked():
                return "invite revoked"
        return None
    return "invalid role"


@router.websocket("/ws/signaling/{match_id}")
async def ws_signaling(websocket: WebSocket, match_id: str) -> None:
    role = (websocket.query_params.get("role") or "").strip().lower()
    if role not in {ROLE_PUBLISHER, ROLE_SUBSCRIBER}:
        await websocket.close(code=4400)
        return

    deny = _authorize(websocket, match_id, role)
    if deny:
        await websocket.close(code=4401)
        return

    with SqlAlchemyUnitOfWork() as uow:
        if uow.matches.get(match_id) is None:
            await websocket.close(code=4404)
            return

    peer_id = new_peer_id(role)
    peer, err = await signaling_hub.try_register(
        match_id, peer_id=peer_id, role=role, websocket=websocket
    )
    if err == "full":
        await websocket.close(code=4429)
        return
    if err == "publisher_exists":
        await websocket.close(code=4409)
        return
    if peer is None:
        await websocket.close(code=4500)
        return

    try:
        await websocket.send_json(
            hello_message(role=role, peer_id=peer_id, match_id=match_id)
        )
        if role == ROLE_SUBSCRIBER:
            signaling_hub.publish_peer_joined(match_id, peer)
        elif role == ROLE_PUBLISHER:
            for sub_id in signaling_hub.list_subscribers(match_id):
                await websocket.send_json(
                    {
                        "protocol": 1,
                        "type": "signaling.peer_joined",
                        "peer_id": sub_id,
                        "role": ROLE_SUBSCRIBER,
                    }
                )

        while True:
            try:
                get_task = asyncio.create_task(peer.queue.get())
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
                    try:
                        raw = recv_task.result()
                    except WebSocketDisconnect:
                        return
                    except RuntimeError:
                        return
                    await _handle_inbound(match_id, peer_id, raw, websocket)
            except WebSocketDisconnect:
                break
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.info("signaling_ws_disconnected match_id=%s peer_id=%s", match_id, peer_id)
    except asyncio.CancelledError:
        pass
    finally:
        await signaling_hub.unregister(match_id, peer_id)


async def _handle_inbound(
    match_id: str, peer_id: str, raw: str, websocket: WebSocket
) -> None:
    try:
        body: Any = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_json(error_message("invalid JSON"))
        return
    if not isinstance(body, dict):
        await websocket.send_json(error_message("expected object"))
        return
    msg_type = body.get("type")
    if msg_type not in RELAY_TYPES:
        await websocket.send_json(error_message(f"unsupported type: {msg_type}"))
        return
    err = signaling_hub.relay(match_id, sender_id=peer_id, message=body)
    if err:
        await websocket.send_json(error_message(err))
