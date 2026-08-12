"""Tournament CRUD + publish (organizer auth)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.commands.create_tournament_draft import (
    TournamentError,
    create_tournament_draft,
)
from app.application.commands.update_tournament import publish_tournament, update_tournament
from app.domain.tournament.entities import FORMAT_SINGLE_ELIM
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.deps.organizer_auth import RequireOrganizer
from app.presentation.http.middleware.correlation import get_correlation_id

router = APIRouter(prefix="/api/v1/tournaments", tags=["tournaments"])


class CreateTournamentBody(BaseModel):
    name: str = ""
    format: str = FORMAT_SINGLE_ELIM
    settings: dict[str, Any] = Field(default_factory=dict)


class PatchTournamentBody(BaseModel):
    name: str | None = None
    format: str | None = None
    settings: dict[str, Any] | None = None


@router.get("")
def list_tournaments(_session: RequireOrganizer) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        items = [t.to_public_dict() for t in uow.tournaments.list()]
    return {"items": items}


@router.post("")
def create_tournament(
    body: CreateTournamentBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    correlation_id = get_correlation_id()
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = create_tournament_draft(
                uow,
                name=body.name,
                format=body.format,
                settings=body.settings,
                correlation_id=correlation_id or None,
            )
    except TournamentError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return result["tournament"]


@router.get("/{tournament_id}")
def get_tournament(tournament_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        tournament = uow.tournaments.get(tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="tournament not found")
    return tournament.to_public_dict()


@router.patch("/{tournament_id}")
def patch_tournament(
    tournament_id: str,
    body: PatchTournamentBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    correlation_id = get_correlation_id()
    try:
        with SqlAlchemyUnitOfWork() as uow:
            tournament = update_tournament(
                uow,
                tournament_id=tournament_id,
                name=body.name,
                format=body.format,
                settings=body.settings,
                correlation_id=correlation_id or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TournamentError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return tournament.to_public_dict()


@router.post("/{tournament_id}/publish")
def post_publish(tournament_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    correlation_id = get_correlation_id()
    try:
        with SqlAlchemyUnitOfWork() as uow:
            tournament = publish_tournament(
                uow,
                tournament_id=tournament_id,
                correlation_id=correlation_id or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TournamentError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return tournament.to_public_dict()
