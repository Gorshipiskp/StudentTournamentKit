"""Issue Pause/Resume/Forfeit to game endpoint; track desired vs actual."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.application.commands.finalize_demo import finalize_match_demo
from app.application.unit_of_work import UnitOfWork
from app.domain.match.entities import MATCH_FORFEITED, Match
from app.domain.match.game_command import (
    CMD_CONFIRMED,
    CMD_FAILED,
    CMD_REQUESTED,
    CMD_SENT,
    TYPE_FORFEIT,
    TYPE_PAUSE,
    TYPE_RESUME,
    TYPE_SNAPSHOT,
    GameCommand,
)
from app.infrastructure.adapters.cs2.command_client import (
    CommandAck,
    GameCommandTransport,
    HttpGameCommandTransport,
)

_ALLOWED = {TYPE_PAUSE, TYPE_RESUME, TYPE_FORFEIT, TYPE_SNAPSHOT}


def issue_match_command(
    uow: UnitOfWork,
    *,
    match_id: str,
    command_type: str,
    payload: dict[str, Any] | None = None,
    command_id: str | None = None,
    correlation_id: str | None = None,
    transport: GameCommandTransport | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    """Create/send game command. Idempotent on command_id.

    Success for clients = ack confirmed — not merely HTTP 200 / delivery_ok.
    """
    if command_type not in _ALLOWED:
        raise ValueError(f"unsupported command type: {command_type}")

    payload = dict(payload or {})
    cid = command_id or str(uuid4())

    existing = uow.game_commands.get(cid)
    if existing is not None:
        match = uow.matches.get(match_id)
        return _response(
            existing,
            match,
            idempotent_replay=True,
            note="same command_id returned without re-send",
        )

    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError("match not found")

    # Desired intent before / as we send (A3 / desired ≠ actual until observed)
    if command_type == TYPE_PAUSE:
        match.desired_paused = True
    elif command_type == TYPE_RESUME:
        match.desired_paused = False

    cmd = GameCommand(
        command_id=cid,
        match_id=match_id,
        command_type=command_type,
        status=CMD_REQUESTED,
        payload=payload,
        correlation_id=correlation_id,
        created_at=datetime.now(UTC),
    )
    uow.game_commands.add(cmd)
    uow.matches.save(match)
    # Persist desired + requested before network call
    flush = getattr(uow, "flush", None)
    if callable(flush):
        flush()

    endpoint = match.game_endpoint_url
    if not endpoint:
        cmd.status = CMD_FAILED
        cmd.ack_status = "failed"
        cmd.ack_error = "game_endpoint_url not configured"
        cmd.ack_at = datetime.now(UTC)
        uow.game_commands.save(cmd)
        if commit:
            uow.commit()
        return _response(cmd, match, note="set game_endpoint_url on match")

    client = transport or HttpGameCommandTransport()
    ack = client.send(
        endpoint_base=endpoint,
        command_id=cid,
        command_type=command_type,
        match_id=match_id,
        server_id=match.game_server_id,
        payload=payload,
        correlation_id=correlation_id,
    )
    _apply_ack(cmd, match, ack)
    demo_info = None
    if (
        cmd.status == CMD_CONFIRMED
        and command_type == TYPE_FORFEIT
        and not uow.demos.list_for_match(match_id)
    ):
        demo = finalize_match_demo(
            uow,
            match_id=match_id,
            map_name=match.map_name,
        )
        demo_info = demo.to_public_dict()
    uow.game_commands.save(cmd)
    uow.matches.save(match)
    if commit:
        uow.commit()
    resp = _response(cmd, match)
    if demo_info is not None:
        resp["demo"] = demo_info
    return resp


def _apply_ack(cmd: GameCommand, match: Match, ack: CommandAck) -> None:
    now = datetime.now(UTC)
    cmd.sent_at = now
    cmd.status = CMD_SENT
    cmd.ack_status = ack.ack_status
    cmd.ack_error = ack.error
    cmd.ack_result = ack.result
    cmd.ack_at = now

    # duplicate from Fake = already applied earlier — treat as confirmed outcome
    if ack.ack_status in {"confirmed", "duplicate"}:
        cmd.status = CMD_CONFIRMED
        if cmd.command_type == TYPE_PAUSE:
            match.actual_paused = True
        elif cmd.command_type == TYPE_RESUME:
            match.actual_paused = False
        elif cmd.command_type == TYPE_FORFEIT:
            match.status = MATCH_FORFEITED
            match.phase = "ended"
            match.actual_paused = False
            match.desired_paused = False
            result = ack.result or {}
            score = result.get("score")
            if isinstance(score, dict):
                a, b = score.get("team_a"), score.get("team_b")
                if isinstance(a, int):
                    match.score_team_a = a
                if isinstance(b, int):
                    match.score_team_b = b
            match.version += 1
    elif ack.ack_status == "failed" or ack.ack_status is None:
        cmd.status = CMD_FAILED
        if not cmd.ack_status:
            cmd.ack_status = "failed"
        if not cmd.ack_error:
            cmd.ack_error = ack.error or "no ack status"
    elif ack.ack_status == "accepted":
        # Delivered but not yet applied — keep SENT; desired set, actual unchanged
        cmd.status = CMD_SENT


def _response(
    cmd: GameCommand,
    match: Match | None,
    *,
    idempotent_replay: bool = False,
    note: str | None = None,
) -> dict[str, Any]:
    pub = cmd.to_public_dict()
    match_pub = match.to_public_dict() if match else None
    return {
        **pub,
        "idempotent_replay": idempotent_replay,
        "note": note,
        "match": match_pub,
        # Explicit: wire success ≠ command success
        "http_200_means_applied": False,
    }
