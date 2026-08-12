"""Unit: generate bracket size=4, assign, match link."""

from __future__ import annotations

import pytest

from app.application.commands.create_tournament_draft import create_tournament_draft
from app.application.commands.manage_bracket import (
    BracketError,
    assign_bracket_slot,
    generate_bracket,
    get_bracket_tree,
)
from app.application.commands.manage_teams import create_team
from tests.fakes import InMemoryUnitOfWork


def _cup_with_teams(n: int = 4) -> tuple:
    uow = InMemoryUnitOfWork()
    tid = create_tournament_draft(uow, name="Cup")["tournament_id"]
    teams = [
        create_team(uow, tournament_id=tid, name=f"T{i}") for i in range(n)
    ]
    return uow, tid, teams


def test_generate_size_4_three_nodes() -> None:
    uow, tid, _teams = _cup_with_teams()
    nodes = generate_bracket(uow, tournament_id=tid, size=4)
    assert len(nodes) == 3
    round0 = [n for n in nodes if n.round == 0]
    finals = [n for n in nodes if n.round == 1]
    assert len(round0) == 2
    assert len(finals) == 1
    assert finals[0].source_a_node_id == round0[0].id
    assert finals[0].source_b_node_id == round0[1].id


def test_assign_creates_matches_when_pair_full() -> None:
    uow, tid, teams = _cup_with_teams()
    generate_bracket(uow, tournament_id=tid, size=4)
    tree = get_bracket_tree(uow, tournament_id=tid)
    sf = [n for n in tree if n.round == 0]
    final = [n for n in tree if n.round == 1][0]

    assign_bracket_slot(
        uow,
        tournament_id=tid,
        node_id=sf[0].id,
        team_a_id=teams[0].id,
        team_b_id=teams[1].id,
    )
    assign_bracket_slot(
        uow,
        tournament_id=tid,
        node_id=sf[1].id,
        team_a_id=teams[2].id,
        team_b_id=teams[3].id,
    )
    # manual winners into final
    assign_bracket_slot(
        uow,
        tournament_id=tid,
        node_id=final.id,
        team_a_id=teams[0].id,
        team_b_id=teams[2].id,
    )

    tree = get_bracket_tree(uow, tournament_id=tid)
    with_match = [n for n in tree if n.match_id]
    assert len(with_match) == 3
    assert len(uow.matches.items) == 3


def test_duplicate_first_round_team_rejected() -> None:
    uow, tid, teams = _cup_with_teams()
    generate_bracket(uow, tournament_id=tid, size=4)
    sf = [n for n in get_bracket_tree(uow, tournament_id=tid) if n.round == 0]
    assign_bracket_slot(
        uow, tournament_id=tid, node_id=sf[0].id, team_a_id=teams[0].id
    )
    with pytest.raises(BracketError, match="first round"):
        assign_bracket_slot(
            uow, tournament_id=tid, node_id=sf[1].id, team_a_id=teams[0].id
        )


def test_bad_size() -> None:
    uow, tid, _ = _cup_with_teams()
    with pytest.raises(BracketError, match="size"):
        generate_bracket(uow, tournament_id=tid, size=6)
