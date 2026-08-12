"""Register / assign game servers."""

from __future__ import annotations

from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.game_server.entities import (
    SERVER_ASSIGNED,
    SERVER_AVAILABLE,
    GameServer,
)
from app.domain.match.entities import MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED, Match


class RegistryConflict(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def is_fake_server_id(server_id: str | None) -> bool:
    if not server_id:
        return True
    return server_id == "srv_fake" or server_id.startswith("srv_fake")


def create_game_server(
    uow: UnitOfWork,
    *,
    server_id: str | None = None,
    host: str | None = None,
    port: int | None = None,
    endpoint_url: str | None = None,
    webhook_secret: str | None = None,
) -> GameServer:
    sid = server_id or f"srv_{uuid4().hex[:12]}"
    if uow.game_servers.get(sid) is not None:
        raise RegistryConflict(f"server already exists: {sid}")
    server = GameServer(
        id=sid,
        status=SERVER_AVAILABLE,
        host=host,
        port=port,
        endpoint_url=endpoint_url,
        webhook_secret=webhook_secret,
    )
    uow.game_servers.add(server)
    uow.commit()
    return server


def assign_server_to_match(
    uow: UnitOfWork,
    *,
    match_id: str,
    server_id: str,
    commit: bool = True,
    force: bool = False,
) -> Match:
    """
    Bind a registered game-server to a match.

    force=True: steal server from another match (local smoke / live-cs2-local).
    Clears previous match.game_server_id when it pointed at this server.
    """
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError("match not found")
    server = uow.game_servers.get(server_id)
    if server is None:
        raise KeyError("server not found")
    if server.status == SERVER_ASSIGNED and server.assigned_match_id not in {
        None,
        match_id,
    }:
        if not force:
            raise RegistryConflict(
                f"server already assigned to match {server.assigned_match_id}"
            )
        prev_match = uow.matches.get(server.assigned_match_id)
        if prev_match is not None and prev_match.game_server_id == server.id:
            prev_match.game_server_id = None
            uow.matches.save(prev_match)
        server.status = SERVER_AVAILABLE
        server.assigned_match_id = None
        uow.game_servers.save(server)

    # Allow replace when unset / Fake; block stealing a real live binding
    if (
        match.game_server_id
        and match.game_server_id != server_id
        and match.status != MATCH_SCHEDULED
        and not is_fake_server_id(match.game_server_id)
    ):
        if not force:
            raise RegistryConflict(
                f"match already has server {match.game_server_id}"
            )

    if match.game_server_id and match.game_server_id != server_id:
        prev = uow.game_servers.get(match.game_server_id)
        if prev is not None and prev.assigned_match_id == match_id:
            prev.status = SERVER_AVAILABLE
            prev.assigned_match_id = None
            uow.game_servers.save(prev)

    match.game_server_id = server.id
    if server.webhook_secret:
        match.webhook_secret = server.webhook_secret
    if server.endpoint_url:
        match.game_endpoint_url = server.endpoint_url
    if match.status == MATCH_SCHEDULED:
        match.status = MATCH_SERVER_ASSIGNED
        match.version += 1

    server.status = SERVER_ASSIGNED
    server.assigned_match_id = match.id
    uow.matches.save(match)
    uow.game_servers.save(server)
    if commit:
        uow.commit()
    return match
