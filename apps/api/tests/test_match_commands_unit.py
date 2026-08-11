"""Unit: pause/resume/forfeit commands — desired/actual + idempotent command_id."""

from __future__ import annotations

from typing import Any

from app.application.commands.create_match import create_match
from app.application.commands.issue_match_command import issue_match_command
from app.domain.match.game_command import TYPE_PAUSE, TYPE_RESUME
from app.infrastructure.adapters.cs2.command_client import CommandAck
from tests.fakes import InMemoryUnitOfWork


class ScriptedTransport:
    def __init__(self, acks: list[CommandAck]) -> None:
        self.acks = list(acks)
        self.calls: list[dict[str, Any]] = []

    def send(self, **kwargs: Any) -> CommandAck:
        self.calls.append(kwargs)
        if not self.acks:
            return CommandAck(
                http_status=None,
                ack_status="failed",
                error="no scripted ack",
                result=None,
            )
        return self.acks.pop(0)


def test_pause_sets_desired_then_actual_on_confirmed() -> None:
    uow = InMemoryUnitOfWork()
    create_match(
        uow,
        match_id="m1",
        game_server_id="srv",
        game_endpoint_url="http://127.0.0.1:27099",
    )
    transport = ScriptedTransport(
        [
            CommandAck(
                http_status=200,
                ack_status="confirmed",
                error=None,
                result={"paused": True},
            )
        ]
    )
    result = issue_match_command(
        uow,
        match_id="m1",
        command_type=TYPE_PAUSE,
        command_id="cmd-pause-1",
        transport=transport,
    )
    assert result["confirmed"] is True
    assert result["http_200_means_applied"] is False
    assert result["status"] == "confirmed"
    match = uow.matches.get("m1")
    assert match is not None
    assert match.desired_paused is True
    assert match.actual_paused is True
    assert match.to_public_dict()["split_brain"] is False
    assert len(transport.calls) == 1


def test_failed_ack_leaves_split_brain() -> None:
    uow = InMemoryUnitOfWork()
    create_match(
        uow,
        match_id="m2",
        game_endpoint_url="http://127.0.0.1:27099",
    )
    transport = ScriptedTransport(
        [
            CommandAck(
                http_status=200,
                ack_status="failed",
                error="match not loaded",
                result=None,
            )
        ]
    )
    result = issue_match_command(
        uow,
        match_id="m2",
        command_type=TYPE_PAUSE,
        command_id="cmd-fail",
        transport=transport,
    )
    assert result["confirmed"] is False
    assert result["status"] == "failed"
    match = uow.matches.get("m2")
    assert match is not None
    assert match.desired_paused is True
    assert match.actual_paused is False
    assert match.to_public_dict()["split_brain"] is True


def test_command_id_idempotent_no_second_send() -> None:
    uow = InMemoryUnitOfWork()
    create_match(
        uow,
        match_id="m3",
        game_endpoint_url="http://fake",
    )
    transport = ScriptedTransport(
        [
            CommandAck(
                http_status=200,
                ack_status="confirmed",
                error=None,
                result={"paused": True},
            )
        ]
    )
    first = issue_match_command(
        uow,
        match_id="m3",
        command_type=TYPE_PAUSE,
        command_id="same-id",
        transport=transport,
    )
    second = issue_match_command(
        uow,
        match_id="m3",
        command_type=TYPE_PAUSE,
        command_id="same-id",
        transport=transport,
    )
    assert first["confirmed"] is True
    assert second["idempotent_replay"] is True
    assert second["command_id"] == "same-id"
    assert len(transport.calls) == 1


def test_resume_clears_desired_and_actual() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m4", game_endpoint_url="http://fake")
    m = uow.matches.get("m4")
    assert m is not None
    m.desired_paused = True
    m.actual_paused = True
    uow.matches.save(m)

    transport = ScriptedTransport(
        [
            CommandAck(
                http_status=200,
                ack_status="confirmed",
                error=None,
                result={"paused": False},
            )
        ]
    )
    result = issue_match_command(
        uow,
        match_id="m4",
        command_type=TYPE_RESUME,
        command_id="cmd-resume",
        transport=transport,
    )
    assert result["confirmed"] is True
    m2 = uow.matches.get("m4")
    assert m2 is not None
    assert m2.desired_paused is False
    assert m2.actual_paused is False
