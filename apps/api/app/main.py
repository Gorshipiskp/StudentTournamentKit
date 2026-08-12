"""FastAPI entrypoint — StudentTournamentKit API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.outbox.dispatcher import dispatch_pending
from app.presentation.http.middleware.correlation import CorrelationIdMiddleware
from app.presentation.http.routers import (
    auth,
    bracket,
    branding,
    foundation,
    game_servers,
    health,
    internal_cs2,
    invites,
    matches,
    ready,
    teams,
    tournaments,
    turn,
    whip,
)
from app.presentation.ws import agent as agent_ws
from app.presentation.ws import judge as judge_ws
from app.presentation.ws import overlay as overlay_ws
from app.presentation.ws import signaling as signaling_ws

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup replay: unprocessed outbox → handlers (idempotent)
    try:
        count = dispatch_pending()
        logging.getLogger("stk.outbox").info("startup_outbox_replay processed=%s", count)
    except Exception:
        # /health must still work if DB is briefly unavailable; /ready reports DB
        logging.getLogger("stk.outbox").exception("startup_outbox_replay_failed")
    yield


app = FastAPI(title="STK API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(health.router)
app.include_router(ready.router)
app.include_router(foundation.router)
app.include_router(auth.router)
app.include_router(tournaments.router)
app.include_router(teams.router)
app.include_router(bracket.router)
app.include_router(branding.router)
app.include_router(matches.router)
app.include_router(invites.router)
app.include_router(turn.router)
app.include_router(whip.router)
app.include_router(game_servers.router)
app.include_router(internal_cs2.router)
app.include_router(overlay_ws.router)
app.include_router(agent_ws.router)
app.include_router(signaling_ws.router)
app.include_router(judge_ws.router)
