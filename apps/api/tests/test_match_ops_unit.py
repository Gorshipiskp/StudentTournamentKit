"""Unit: Fake start + staff links."""

from __future__ import annotations

from app.application.commands.create_match import create_match
from app.application.commands.create_tournament_draft import create_tournament_draft
from app.application.commands.invite_tokens import redeem_invite
from app.application.commands.staff_links import create_match_staff_links
from app.application.commands.start_match import start_match_fake
from app.domain.match.entities import MATCH_LIVE
from tests.fakes import InMemoryUnitOfWork


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
