"""Game server registry HTTP API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.commands.game_server_registry import (
    RegistryConflict,
    create_game_server,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/api/v1/game-servers", tags=["game-servers"])


class CreateServerBody(BaseModel):
    server_id: str | None = None
    host: str | None = None
    port: int | None = None
    endpoint_url: str | None = None
    webhook_secret: str | None = None


@router.post("")
def post_server(body: CreateServerBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            server = create_game_server(
                uow,
                server_id=body.server_id,
                host=body.host,
                port=body.port,
                endpoint_url=body.endpoint_url,
                webhook_secret=body.webhook_secret,
            )
    except RegistryConflict as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    return server.to_public_dict()


@router.get("")
def list_servers() -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        items = [s.to_public_dict() for s in uow.game_servers.list()]
    return {"items": items}


@router.get("/{server_id}")
def get_server(server_id: str) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        server = uow.game_servers.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="server not found")
    return server.to_public_dict()
