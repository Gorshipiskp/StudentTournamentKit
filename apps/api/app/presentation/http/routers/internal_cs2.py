"""Internal CS2 webhook ingest — HMAC + normalize + Match FSM."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.infrastructure.adapters.cs2.hmac_util import (
    resolve_webhook_secret,
    verify_signature,
)
from app.infrastructure.adapters.cs2.normalize import NormalizeError, normalize_cs2_event
from app.infrastructure.outbox.dispatcher import dispatch_pending
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.middleware.correlation import get_correlation_id

router = APIRouter(prefix="/api/v1/internal/cs2", tags=["internal-cs2"])


@router.post("/events")
async def post_cs2_events(
    request: Request,
    x_stk_signature: str | None = Header(default=None, alias="X-STK-Signature"),
) -> dict[str, Any]:
    raw = await request.body()
    try:
        body = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be object")

    try:
        event = normalize_cs2_event(body)
    except NormalizeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with SqlAlchemyUnitOfWork() as uow:
        match = uow.matches.get(event["match_id"])
        if match is None:
            raise HTTPException(status_code=404, detail="match not found")

        secret = resolve_webhook_secret(match.webhook_secret)
        if not secret:
            raise HTTPException(
                status_code=500,
                detail="webhook secret not configured for match",
            )
        if not verify_signature(secret, raw, x_stk_signature):
            raise HTTPException(status_code=401, detail="invalid HMAC signature")

        correlation_id = event.get("correlation_id") or get_correlation_id() or None
        result = ingest_cs2_event(
            uow,
            event_id=event["event_id"],
            sequence=event["sequence"],
            server_id=event["server_id"],
            match_id=event["match_id"],
            event_type=event["type"],
            payload=event["payload"],
            correlation_id=correlation_id,
        )
        if result["status"] == "not_found":
            raise HTTPException(status_code=404, detail="match not found")
        uow.commit()

    if result.get("applied") or result.get("status") == "duplicate":
        # Duplicate still 200; dispatch any new outbox from applied path
        if result.get("applied"):
            dispatch_pending()

    # rejected (OOO etc.) still 200 with applied=false — event_id stored
    return result
