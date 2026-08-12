"""Unit: teams + players CRUD and isolation."""

from __future__ import annotations

import pytest

from app.application.commands.create_tournament_draft import create_tournament_draft
from app.application.commands.manage_teams import (
    TeamError,
    create_player,
    create_team,
    delete_team,
    update_team,
)
from app.domain.tournament.team_entities import MAX_PLAYERS_PER_TEAM
from tests.fakes import InMemoryUnitOfWork


def _two_tournaments() -> tuple[InMemoryUnitOfWork, str, str]:
    uow = InMemoryUnitOfWork()
    a = create_tournament_draft(uow, name="A")["tournament_id"]
    b = create_tournament_draft(uow, name="B")["tournament_id"]
    return uow, a, b


def test_create_four_teams_with_players() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    for i in range(4):
        team = create_team(uow, tournament_id=tid, name=f"Team {i}", tag=f"T{i}")
        create_player(uow, tournament_id=tid, team_id=team.id, nickname=f"p{i}a")
        create_player(uow, tournament_id=tid, team_id=team.id, nickname=f"p{i}b")
    assert uow.teams.count_for_tournament(tid) == 4
    for team in uow.teams.list_for_tournament(tid):
        assert uow.players.count_for_team(team.id) == 2


def test_unique_name_per_tournament() -> None:
    uow, a, b = _two_tournaments()
    create_team(uow, tournament_id=a, name="Alpha")
    with pytest.raises(TeamError, match="already used"):
        create_team(uow, tournament_id=a, name="Alpha")
    # same name ok in other tournament
    create_team(uow, tournament_id=b, name="Alpha")
    assert uow.teams.count_for_tournament(a) == 1
    assert uow.teams.count_for_tournament(b) == 1


def test_player_limit_and_delete_cascades() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    team = create_team(uow, tournament_id=tid, name="Alpha")
    for i in range(MAX_PLAYERS_PER_TEAM):
        create_player(uow, tournament_id=tid, team_id=team.id, nickname=f"n{i}")
    with pytest.raises(TeamError, match="max"):
        create_player(uow, tournament_id=tid, team_id=team.id, nickname="extra")
    delete_team(uow, tournament_id=tid, team_id=team.id)
    assert uow.teams.get(team.id) is None
    assert uow.players.count_for_team(team.id) == 0


def test_rename_team() -> None:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    team = create_team(uow, tournament_id=tid, name="Old")
    updated = update_team(uow, tournament_id=tid, team_id=team.id, name="New", tag="N")
    assert updated.name == "New"
    assert updated.tag == "N"
