"""Tournament teams + players API (organizer auth)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.application.commands.manage_teams import (
    TeamError,
    create_player,
    create_team,
    delete_player,
    delete_team,
    update_player,
    update_team,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.deps.organizer_auth import RequireOrganizer

router = APIRouter(prefix="/api/v1/tournaments", tags=["teams"])


class CreateTeamBody(BaseModel):
    name: str
    tag: str = ""


class PatchTeamBody(BaseModel):
    name: str | None = None
    tag: str | None = None


class CreatePlayerBody(BaseModel):
    nickname: str
    steam_id: str | None = None
    is_coach: bool = False


class PatchPlayerBody(BaseModel):
    nickname: str | None = None
    steam_id: str | None = None
    is_coach: bool | None = None


def _http_team_error(exc: TeamError) -> HTTPException:
    return HTTPException(status_code=400, detail=exc.message)


@router.get("/{tournament_id}/teams")
def list_teams(tournament_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        if uow.tournaments.get(tournament_id) is None:
            raise HTTPException(status_code=404, detail="tournament not found")
        teams = uow.teams.list_for_tournament(tournament_id)
        items = []
        for t in teams:
            players = [p.to_public_dict() for p in uow.players.list_for_team(t.id)]
            items.append({**t.to_public_dict(), "players": players})
    return {"items": items}


@router.post("/{tournament_id}/teams")
def post_team(
    tournament_id: str,
    body: CreateTeamBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            team = create_team(
                uow,
                tournament_id=tournament_id,
                name=body.name,
                tag=body.tag,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TeamError as exc:
        raise _http_team_error(exc) from exc
    return {**team.to_public_dict(), "players": []}


@router.patch("/{tournament_id}/teams/{team_id}")
def patch_team(
    tournament_id: str,
    team_id: str,
    body: PatchTeamBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            team = update_team(
                uow,
                tournament_id=tournament_id,
                team_id=team_id,
                name=body.name,
                tag=body.tag,
            )
            players = [p.to_public_dict() for p in uow.players.list_for_team(team.id)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TeamError as exc:
        raise _http_team_error(exc) from exc
    return {**team.to_public_dict(), "players": players}


@router.delete("/{tournament_id}/teams/{team_id}")
def remove_team(
    tournament_id: str,
    team_id: str,
    _session: RequireOrganizer,
) -> dict[str, bool]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            delete_team(uow, tournament_id=tournament_id, team_id=team_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/{tournament_id}/teams/{team_id}/players")
def post_player(
    tournament_id: str,
    team_id: str,
    body: CreatePlayerBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            player = create_player(
                uow,
                tournament_id=tournament_id,
                team_id=team_id,
                nickname=body.nickname,
                steam_id=body.steam_id,
                is_coach=body.is_coach,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TeamError as exc:
        raise _http_team_error(exc) from exc
    return player.to_public_dict()


@router.patch("/{tournament_id}/teams/{team_id}/players/{player_id}")
def patch_player(
    tournament_id: str,
    team_id: str,
    player_id: str,
    body: PatchPlayerBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            player = update_player(
                uow,
                tournament_id=tournament_id,
                team_id=team_id,
                player_id=player_id,
                nickname=body.nickname,
                steam_id=body.steam_id,
                is_coach=body.is_coach,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TeamError as exc:
        raise _http_team_error(exc) from exc
    return player.to_public_dict()


@router.delete("/{tournament_id}/teams/{team_id}/players/{player_id}")
def remove_player(
    tournament_id: str,
    team_id: str,
    player_id: str,
    _session: RequireOrganizer,
) -> dict[str, bool]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            delete_player(
                uow,
                tournament_id=tournament_id,
                team_id=team_id,
                player_id=player_id,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}
