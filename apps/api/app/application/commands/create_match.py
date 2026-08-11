"""CreateMatch — platform match row for Fake / Bridge ingest."""

from __future__ import annotations

from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.match.entities import MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED, Match


def create_match(
    uow: UnitOfWork,
    *,
    tournament_id: str | None = None,
    match_id: str | None = None,
    game_server_id: str | None = None,
    webhook_secret: str | None = None,
    map_name: str | None = None,
    game_endpoint_url: str | None = None,
) -> Match:
    tid = tournament_id or str(uuid4())
    # Ensure tournament exists for FK (flush before match insert on SQLAlchemy)
    if uow.tournaments.get(tid) is None:
        from app.domain.tournament.entities import Tournament

        uow.tournaments.add(Tournament(id=tid, status="draft"))
        flush = getattr(uow, "flush", None)
        if callable(flush):
            flush()

    mid = match_id or str(uuid4())
    if uow.matches.get(mid) is not None:
        raise ValueError(f"match already exists: {mid}")

    status = MATCH_SERVER_ASSIGNED if game_server_id else MATCH_SCHEDULED
    match = Match(
        id=mid,
        tournament_id=tid,
        status=status,
        game_server_id=game_server_id,
        webhook_secret=webhook_secret,
        map_name=map_name,
        game_endpoint_url=game_endpoint_url,
    )
    uow.matches.add(match)
    uow.commit()
    return match
