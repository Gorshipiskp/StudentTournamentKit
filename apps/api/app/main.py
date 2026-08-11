"""FastAPI entrypoint — Student Tournament Platform API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.outbox.dispatcher import dispatch_pending
from app.presentation.http.middleware.correlation import CorrelationIdMiddleware
from app.presentation.http.routers import (
    foundation,
    game_servers,
    health,
    internal_cs2,
    matches,
    ready,
)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup replay: unprocessed outbox → handlers (idempotent)
    try:
        count = dispatch_pending()
        logging.getLogger("stp.outbox").info("startup_outbox_replay processed=%s", count)
    except Exception:
        # /health must still work if DB is briefly unavailable; /ready reports DB
        logging.getLogger("stp.outbox").exception("startup_outbox_replay_failed")
    yield


app = FastAPI(title="STP API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(health.router)
app.include_router(ready.router)
app.include_router(foundation.router)
app.include_router(matches.router)
app.include_router(game_servers.router)
app.include_router(internal_cs2.router)
