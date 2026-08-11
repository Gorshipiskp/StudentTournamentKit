"""Unit: registry assign + snapshot reconcile after sequence gap."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.create_match import create_match
from app.application.commands.game_server_registry import (
    assign_server_to_match,
    create_game_server,
)
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.application.commands.reconcile_match import reconcile_match_from_snapshot
from app.domain.game_server.entities import SERVER_ASSIGNED
from app.domain.match.entities import MATCH_SERVER_ASSIGNED
from app.infrastructure.adapters.cs2.command_client import CommandAck
from tests.fakes import InMemoryUnitOfWork


class SnapshotTransport:
    def __init__(self, snapshot: dict[str, Any]) -> None:
        self.snapshot = snapshot
        self.calls: list[dict[str, Any]] = []

    def send(self, **kwargs: Any) -> CommandAck:
        self.calls.append(kwargs)
        assert kwargs["command_type"] == "GetSnapshot"
        return CommandAck(
            http_status=200,
            ack_status="confirmed",
            error=None,
            result={"snapshot": self.snapshot},
        )


def test_assign_server_copies_endpoint_and_secret() -> None:
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m1")
    create_game_server(
        uow,
        server_id="srv1",
        endpoint_url="http://127.0.0.1:27099",
        webhook_secret="sec",
        host="127.0.0.1",
        port=27099,
    )
    match = assign_server_to_match(uow, match_id="m1", server_id="srv1")
    assert match.game_server_id == "srv1"
    assert match.game_endpoint_url == "http://127.0.0.1:27099"
    assert match.webhook_secret == "sec"
    assert match.status == MATCH_SERVER_ASSIGNED
    server = uow.game_servers.get("srv1")
    assert server is not None
    assert server.status == SERVER_ASSIGNED
    assert server.assigned_match_id == "m1"


def test_reconcile_repairs_score_after_missed_events() -> None:
    uow = InMemoryUnitOfWork()
    create_match(
        uow,
        match_id="m2",
        game_server_id="srv2",
        game_endpoint_url="http://fake",
    )
    create_game_server(uow, server_id="srv2", endpoint_url="http://fake")

    # Platform saw only seq 1; Fake is already at score 5-2 seq 8
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv2",
        match_id="m2",
        event_type="round_end",
        payload={"round": 1, "score": {"team_a": 1, "team_b": 0}},
    )
    uow.commit()
    m = uow.matches.get("m2")
    assert m is not None
    assert m.score_team_a == 1
    assert m.last_sequence == 1

    # Simulate gap detection without applying missing history
    m.reconcile_needed = True
    uow.matches.save(m)

    transport = SnapshotTransport(
        {
            "match_id": "m2",
            "server_id": "srv2",
            "map": "de_mirage",
            "round": 7,
            "score": {"team_a": 5, "team_b": 2},
            "phase": "freeze",
            "paused": False,
            "loaded": True,
            "completed": False,
            "last_sequence": 8,
            "players": [],
        }
    )
    result = reconcile_match_from_snapshot(
        uow, match_id="m2", transport=transport
    )
    assert result["ok"] is True
    assert "score" in result["changed"]
    assert "last_sequence" in result["changed"]
    repaired = uow.matches.get("m2")
    assert repaired is not None
    assert repaired.score_team_a == 5
    assert repaired.score_team_b == 2
    assert repaired.round_number == 7
    assert repaired.last_sequence == 8
    assert repaired.reconcile_needed is False
    assert repaired.map_name == "de_mirage"


def test_heartbeat_updates_server_last_heartbeat() -> None:
    uow = InMemoryUnitOfWork()
    create_game_server(uow, server_id="srv_hb", endpoint_url="http://x")
    create_match(
        uow,
        match_id="m_hb",
        game_server_id="srv_hb",
        game_endpoint_url="http://x",
    )
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv_hb",
        match_id="m_hb",
        event_type="heartbeat",
        payload={"bridge_version": "fake-cs2/0.1.0", "protocol_version": "1"},
    )
    uow.commit()
    server = uow.game_servers.get("srv_hb")
    assert server is not None
    assert server.last_heartbeat is not None
    assert server.bridge_version == "fake-cs2/0.1.0"
    assert server.protocol_version == "1"
