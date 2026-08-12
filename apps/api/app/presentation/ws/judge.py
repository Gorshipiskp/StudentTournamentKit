"""WebSocket: judge panel match.status channel."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.identity.caps import CAP_JUDGE_REVIEW
from app.domain.match.messages import PROTOCOL_VERSION, TYPE_MATCH_STATUS
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime.judge_hub import judge_hub
from app.infrastructure.security.session_token import parse_session_token

logger = logging.getLogger("stk.ws.judge")

router = APIRouter(tags=["judge-ws"])


def _extract_token(websocket: WebSocket) -> str | None:
    q = websocket.query_params.get("token") or websocket.query_params.get("access_token")
    if q:
        return q
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


@router.websocket("/ws/judge/{match_id}")
async def ws_judge(websocket: WebSocket, match_id: str) -> None:
    token = _extract_token(websocket)
    if not token:
        await websocket.close(code=4401)
        return
    try:
        session = parse_session_token(token)
    except ValueError:
        await websocket.close(code=4401)
        return
    if not session.requires_match(match_id) or not session.has_cap(CAP_JUDGE_REVIEW):
        await websocket.close(code=4403)
        return

    with SqlAlchemyUnitOfWork() as uow:
        invite = uow.invites.get(session.invite_id)
        if invite is None or invite.is_revoked():
            await websocket.close(code=4401)
            return
        match = uow.matches.get(match_id)
        if match is None:
            await websocket.close(code=4404)
            return
        initial = {
            "protocol": PROTOCOL_VERSION,
            "type": TYPE_MATCH_STATUS,
            "match_id": match_id,
            "reason": "snapshot",
            "match": match.to_public_dict(),
        }

    queue = await judge_hub.connect(match_id, websocket)
    try:
        await websocket.send_json(initial)
        while True:
            try:
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
                    try:
                        _ = recv_task.result()
                    except WebSocketDisconnect:
                        return
                    except RuntimeError:
                        return
            except WebSocketDisconnect:
                break
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.info("judge_ws_disconnected match_id=%s", match_id)
    finally:
        await judge_hub.disconnect(match_id, websocket, queue)
