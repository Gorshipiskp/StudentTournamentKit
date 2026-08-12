"""Match HTTP API — create, get, game commands (Game Slice)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.application.commands.create_match import create_match
from app.application.commands.game_server_registry import (
    RegistryConflict,
    assign_server_to_match,
)
from app.application.commands.issue_match_command import issue_match_command
from app.application.commands.judge_review import (
    JudgeConflict,
    cancel_review,
    request_review,
    resolve_review,
)
from app.application.commands.reconcile_match import reconcile_match_from_snapshot
from app.application.commands.rebuild_overlay import apply_overlay_override, get_overlay_message
from app.application.commands.staff_links import create_match_staff_links
from app.application.commands.start_match import MatchStartError, start_match_fake
from app.application.commands.update_production import (
    ProductionConflict,
    get_production,
    patch_production,
)
from app.domain.identity.caps import CAP_JUDGE_RESOLVE, CAP_JUDGE_REVIEW
from app.domain.identity.entities import InviteSession
from app.domain.match.game_command import TYPE_FORFEIT, TYPE_PAUSE, TYPE_RESUME
from app.infrastructure.outbox.dispatcher import dispatch_pending
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.http.deps.invite_auth import require_match_caps
from app.presentation.http.deps.organizer_auth import RequireOrganizer
from app.presentation.http.middleware.correlation import get_correlation_id

router = APIRouter(prefix="/api/v1/matches", tags=["matches"])


class CreateMatchBody(BaseModel):
    tournament_id: str | None = None
    match_id: str | None = None
    game_server_id: str | None = None
    webhook_secret: str | None = None
    map_name: str | None = None
    game_endpoint_url: str | None = Field(
        default=None,
        description="Fake/Bridge base URL, e.g. http://127.0.0.1:27099",
    )


class CommandBody(BaseModel):
    command_id: str | None = None
    reason: str | None = None
    losing_team: str | None = None  # forfeit only: team_a | team_b


class ResolveBody(BaseModel):
    action: str  # continue | forfeit
    version: int
    losing_team: str | None = None


class AssignServerBody(BaseModel):
    server_id: str


class ProductionPatchBody(BaseModel):
    desired_scene: str | None = None
    desired_stream: str | None = None


class OverlayOverrideBody(BaseModel):
    team_a_name: str | None = None
    team_b_name: str | None = None
    score_team_a: int | None = None
    score_team_b: int | None = None
    map: str | None = None
    round: int | None = None
    judge_banner: str | None = None
    clear: bool = False


@router.post("")
def post_match(body: CreateMatchBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            match = create_match(
                uow,
                tournament_id=body.tournament_id,
                match_id=body.match_id,
                game_server_id=body.game_server_id,
                webhook_secret=body.webhook_secret,
                map_name=body.map_name,
                game_endpoint_url=body.game_endpoint_url,
            )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return match.to_public_dict()


@router.get("/{match_id}")
def get_match(match_id: str) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        match = uow.matches.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    return match.to_public_dict()


@router.post("/{match_id}/start")
def post_match_start(match_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    """Fake/admin start — marks match live without CS2 VPS (TZ005 P5)."""
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = start_match_fake(
                uow,
                match_id=match_id,
                correlation_id=get_correlation_id() or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MatchStartError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except ProductionConflict as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    dispatch_pending()
    return result


@router.post("/{match_id}/staff-links")
def post_staff_links(match_id: str, _session: RequireOrganizer) -> dict[str, Any]:
    """Create judge + commentator invites and deep-link URLs for organizer."""
    try:
        with SqlAlchemyUnitOfWork() as uow:
            return create_match_staff_links(uow, match_id=match_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{match_id}/production")
def get_match_production(match_id: str) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            body = get_production(uow, match_id=match_id)
            uow.commit()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return body


@router.patch("/{match_id}/production")
def patch_match_production(
    match_id: str, body: ProductionPatchBody
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = patch_production(
                uow,
                match_id=match_id,
                desired_scene=body.desired_scene,
                desired_stream=body.desired_stream,
                correlation_id=get_correlation_id() or None,
            )
            uow.commit()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProductionConflict as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    dispatch_pending()
    return result


@router.get("/{match_id}/overlay")
def get_match_overlay(match_id: str) -> dict[str, Any]:
    """Current overlay.snapshot (full state, DB-backed version)."""
    with SqlAlchemyUnitOfWork() as uow:
        message = get_overlay_message(uow, match_id)
        if message is None:
            raise HTTPException(status_code=404, detail="match not found")
        uow.commit()
    return message


@router.post("/{match_id}/overlay/override")
def post_overlay_override(
    match_id: str, body: OverlayOverrideBody
) -> dict[str, Any]:
    """Manual overlay override (director). Never talks to OBS."""
    patch = body.model_dump(exclude_none=True, exclude={"clear"})
    try:
        with SqlAlchemyUnitOfWork() as uow:
            message = apply_overlay_override(
                uow,
                match_id=match_id,
                patch=patch if not body.clear else None,
                clear=body.clear,
                correlation_id=get_correlation_id() or None,
            )
            uow.commit()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dispatch_pending()
    return message


@router.get("/{match_id}/snapshot")
def get_match_platform_snapshot(match_id: str) -> dict[str, Any]:
    """Platform view of match (not live CS2 snapshot)."""
    with SqlAlchemyUnitOfWork() as uow:
        match = uow.matches.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    pub = match.to_public_dict()
    return {
        "match_id": pub["id"],
        "server_id": pub["game_server_id"],
        "map": pub["map"],
        "round": pub["round"],
        "score": pub["score"],
        "phase": pub["phase"],
        "paused": pub["actual_paused"],
        "last_sequence": pub["last_sequence"],
        "reconcile_needed": pub["reconcile_needed"],
        "source": "platform",
    }


@router.get("/{match_id}/demos")
def get_match_demos(match_id: str) -> dict[str, Any]:
    with SqlAlchemyUnitOfWork() as uow:
        match = uow.matches.get(match_id)
        if match is None:
            raise HTTPException(status_code=404, detail="match not found")
        items = [d.to_public_dict() for d in uow.demos.list_for_match(match_id)]
    return {"match_id": match_id, "items": items}


@router.post("/{match_id}/assign-server")
def post_assign_server(match_id: str, body: AssignServerBody) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            match = assign_server_to_match(
                uow, match_id=match_id, server_id=body.server_id
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegistryConflict as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    return match.to_public_dict()


@router.post("/{match_id}/reconcile")
def post_reconcile(match_id: str) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            return reconcile_match_from_snapshot(
                uow,
                match_id=match_id,
                correlation_id=get_correlation_id() or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _issue(match_id: str, command_type: str, body: CommandBody) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if body.reason:
        payload["reason"] = body.reason
    if command_type == TYPE_FORFEIT:
        if body.losing_team not in {"team_a", "team_b"}:
            raise HTTPException(
                status_code=400,
                detail="losing_team must be team_a or team_b",
            )
        payload["losing_team"] = body.losing_team

    try:
        with SqlAlchemyUnitOfWork() as uow:
            return issue_match_command(
                uow,
                match_id=match_id,
                command_type=command_type,
                payload=payload,
                command_id=body.command_id,
                correlation_id=get_correlation_id() or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{match_id}/commands/pause")
def post_pause(match_id: str, body: CommandBody | None = None) -> dict[str, Any]:
    return _issue(match_id, TYPE_PAUSE, body or CommandBody())


@router.post("/{match_id}/commands/resume")
def post_resume(match_id: str, body: CommandBody | None = None) -> dict[str, Any]:
    return _issue(match_id, TYPE_RESUME, body or CommandBody())


@router.post("/{match_id}/commands/forfeit")
def post_forfeit(match_id: str, body: CommandBody) -> dict[str, Any]:
    return _issue(match_id, TYPE_FORFEIT, body)


@router.post("/{match_id}/judge/review-request")
def post_review_request(
    match_id: str,
    _session: Annotated[InviteSession, Depends(require_match_caps(CAP_JUDGE_REVIEW))],
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            match = request_review(uow, match_id=match_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JudgeConflict as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    dispatch_pending()
    return match.to_public_dict()


@router.post("/{match_id}/judge/review-cancel")
def post_review_cancel(
    match_id: str,
    _session: Annotated[InviteSession, Depends(require_match_caps(CAP_JUDGE_REVIEW))],
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            match = cancel_review(uow, match_id=match_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JudgeConflict as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    dispatch_pending()
    return match.to_public_dict()


@router.post("/{match_id}/judge/review-resolve")
def post_review_resolve(
    match_id: str,
    body: ResolveBody,
    _session: Annotated[InviteSession, Depends(require_match_caps(CAP_JUDGE_RESOLVE))],
) -> dict[str, Any]:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = resolve_review(
                uow,
                match_id=match_id,
                action=body.action,
                expected_version=body.version,
                losing_team=body.losing_team,
                correlation_id=get_correlation_id() or None,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JudgeConflict as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    dispatch_pending()
    return result
