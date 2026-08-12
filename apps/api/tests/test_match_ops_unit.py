"""Unit: Fake start + staff links."""

from __future__ import annotations

from app.application.commands.create_match import create_match
from app.application.commands.create_tournament_draft import create_tournament_draft
from app.application.commands.invite_tokens import redeem_invite
from app.application.commands.staff_links import create_match_staff_links
from app.application.commands.start_match import start_match_fake
from app.domain.match.entities import MATCH_LIVE
from tests.fakes import InMemoryUnitOfWork


def test_sync_match_scoreboard_updates_match_and_overlay() -> None:
    from app.application.commands.rebuild_overlay import apply_overlay_override
    from app.application.commands.sync_match_scoreboard import sync_match_scoreboard

    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_score_sync")
    apply_overlay_override(
        uow,
        match_id=match.id,
        patch={"score_team_a": 9, "score_team_b": 9, "round": 99},
    )
    result = sync_match_scoreboard(
        uow,
        match_id=match.id,
        from_server=False,
        score_team_a=3,
        score_team_b=1,
        round_number=5,
    )
    saved = uow.matches.get(match.id)
    assert saved is not None
    assert saved.score_team_a == 3
    assert saved.score_team_b == 1
    assert saved.round_number == 5
    ov = uow.overlays.get(match.id)
    assert ov is not None
    assert "score_team_a" not in ov.manual_overrides
    assert ov.data["team_a"]["score"] == 3
    assert ov.data["team_b"]["score"] == 1
    assert ov.data["round"] == 5
    assert result["match"]["score"]["team_a"] == 3
    assert result["source"] == "manual"


def test_sync_match_scoreboard_from_server_snapshot() -> None:
    from app.application.commands.game_server_registry import (
        assign_server_to_match,
        create_game_server,
    )
    from app.application.commands.rebuild_overlay import apply_overlay_override
    from app.application.commands.sync_match_scoreboard import sync_match_scoreboard
    from app.infrastructure.adapters.cs2.command_client import CommandAck

    class SnapshotTransport:
        def send(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["command_type"] == "GetSnapshot"
            return CommandAck(
                http_status=200,
                ack_status="confirmed",
                error=None,
                result={
                    "snapshot": {
                        "score": {"team_a": 0, "team_b": 0},
                        "round": 0,
                        "phase": "warmup",
                        "map": "de_mirage",
                    }
                },
            )

    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_score_srv")
    create_game_server(
        uow,
        server_id="srv_sync",
        endpoint_url="http://127.0.0.1:27099",
        webhook_secret="sec",
    )
    assign_server_to_match(uow, match_id=match.id, server_id="srv_sync")
    m = uow.matches.get(match.id)
    assert m is not None
    m.score_team_a = 0
    m.score_team_b = 1
    m.round_number = 6
    m.phase = "live"
    uow.matches.save(m)
    apply_overlay_override(
        uow,
        match_id=match.id,
        patch={"score_team_a": 0, "score_team_b": 1, "round": 6},
    )

    result = sync_match_scoreboard(
        uow,
        match_id=match.id,
        from_server=True,
        transport=SnapshotTransport(),
    )
    saved = uow.matches.get(match.id)
    assert saved is not None
    assert saved.score_team_a == 0
    assert saved.score_team_b == 0
    assert saved.round_number == 0
    assert saved.phase == "warmup"
    ov = uow.overlays.get(match.id)
    assert ov is not None
    assert "score_team_a" not in ov.manual_overrides
    assert ov.data["team_a"]["score"] == 0
    assert ov.data["team_b"]["score"] == 0
    assert ov.data["round"] == 0
    assert result["source"] == "server"


def test_start_match_fake_sets_live() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    match = create_match(uow, tournament_id=tid, match_id="m_start")
    result = start_match_fake(uow, match_id=match.id)
    assert result["match"]["status"] == MATCH_LIVE
    assert result["mode"] == "fake"
    assert uow.matches.get(match.id).game_server_id == "srv_fake"
    prod = uow.production.get(match.id)
    assert prod is not None
    assert prod.desired_scene == "ingame"


def test_start_match_live_requires_server() -> None:
    from app.application.commands.start_match import MatchStartError, start_match_live

    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    create_match(uow, tournament_id=tid, match_id="m_live_need")
    try:
        start_match_live(uow, match_id="m_live_need", send_load_match=False)
        raise AssertionError("expected MatchStartError")
    except MatchStartError as exc:
        assert exc.code == "no_live_server"


def test_start_match_live_auto_assigns_srv_local() -> None:
    from app.application.commands.game_server_registry import create_game_server
    from app.application.commands.start_match import start_match_live

    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    create_match(uow, tournament_id=tid, match_id="m_bracket")
    create_game_server(
        uow,
        server_id="srv_local",
        endpoint_url="http://127.0.0.1:27099",
        webhook_secret="sec_auto",
        host="127.0.0.1",
        port=27015,
    )
    result = start_match_live(
        uow, match_id="m_bracket", send_load_match=False
    )
    assert result["mode"] == "live"
    assert result["match"]["game_server_id"] == "srv_local"
    assert uow.matches.get("m_bracket").game_endpoint_url == "http://127.0.0.1:27099"


def test_start_match_live_with_assigned_server() -> None:
    from app.application.commands.game_server_registry import (
        assign_server_to_match,
        create_game_server,
    )
    from app.application.commands.start_match import start_match_live
    from app.infrastructure.adapters.cs2.command_client import CommandAck

    class _OkTransport:
        def send(self, **_kwargs):  # type: ignore[no-untyped-def]
            return CommandAck(
                http_status=200,
                ack_status="confirmed",
                error=None,
                result={"stub": True},
            )

    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    create_match(uow, tournament_id=tid, match_id="m_live_ok")
    create_game_server(
        uow,
        server_id="srv_local",
        endpoint_url="http://127.0.0.1:27099",
        webhook_secret="sec_live_test",
        host="127.0.0.1",
        port=27015,
    )
    assign_server_to_match(uow, match_id="m_live_ok", server_id="srv_local")
    result = start_match_live(
        uow,
        match_id="m_live_ok",
        transport=_OkTransport(),
    )
    assert result["mode"] == "live"
    assert result["match"]["status"] == MATCH_LIVE
    assert result["match"]["game_server_id"] == "srv_local"
    assert result["bridge_config"]["MatchId"] == "m_live_ok"
    assert result["bridge_config"]["ServerId"] == "srv_local"
    assert result["load_match"]["ack_status"] == "confirmed"
    # Fake path still intact
    m2 = create_match(uow, tournament_id=tid, match_id="m_fake_still")
    fake = start_match_fake(uow, match_id=m2.id)
    assert fake["mode"] == "fake"
    assert uow.matches.get(m2.id).game_server_id == "srv_fake"


def test_staff_links_redeem_judge() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    create_match(uow, tournament_id=tid, match_id="m_links")
    pack = create_match_staff_links(uow, match_id="m_links")
    assert pack["director_url"].endswith("/director/m_links")
    assert "token=" in pack["judge"]["url"]
    assert "watch?token=" in pack["commentator"]["url"]

    redeemed = redeem_invite(uow, raw_token=pack["judge"]["token"])
    assert redeemed.session.role == "judge"
    assert redeemed.session.match_id == "m_links"
