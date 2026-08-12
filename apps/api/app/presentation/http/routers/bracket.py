"""Tournament bracket API (organizer auth)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.application.commands.manage_bracket import (
    BracketError,
    assign_bracket_slot,
    generate_bracket,
    get_bracket_tree,
)
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.deps.organizer_auth import RequireOrganizer

router = APIRouter(prefix="/api/v1/tournaments", tags=["bracket"])


class GenerateBody(BaseModel):
    size: int = 4
    replace: bool = False


class AssignNodeBody(BaseModel):
    team_a_id: str | None = None
    team_b_id: str | None = None
    clear_team_a: bool = False
    clear_team_b: bool = False


@router.get("/{tournament_id}/bracket")
def get_bracket(tournament_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            nodes = get_bracket_tree(uow, tournament_id=tournament_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"items": [n.to_public_dict() for n in nodes]}


@router.post("/{tournament_id}/bracket/generate")
def post_generate(
    tournament_id: str,
    body: GenerateBody,
    _session: RequireOrganizer,
    size: int | None = Query(default=None),
) -> dict[str, Any]:
    # Accept size via query (runbook) or body
    effective_size = size if size is not None else body.size
    try:
        with SqlAlchemyUnitOfWork() as uow:
            nodes = generate_bracket(
                uow,
                tournament_id=tournament_id,
                size=effective_size,
                replace=body.replace,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BracketError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return {"items": [n.to_public_dict() for n in nodes]}


@router.patch("/{tournament_id}/bracket/nodes/{node_id}")
def patch_node(
    tournament_id: str,
    node_id: str,
    body: AssignNodeBody,
    _session: RequireOrganizer,
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            node = assign_bracket_slot(
                uow,
                tournament_id=tournament_id,
                node_id=node_id,
                team_a_id=body.team_a_id,
                team_b_id=body.team_b_id,
                clear_team_a=body.clear_team_a,
                clear_team_b=body.clear_team_b,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BracketError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return node.to_public_dict()
