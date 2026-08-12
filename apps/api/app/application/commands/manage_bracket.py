"""Generate / assign single-elim bracket."""

from __future__ import annotations

from math import log2
from uuid import uuid4

from app.application.commands.create_match import create_match
from app.application.unit_of_work import UnitOfWork
from app.domain.match.entities import MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED
from app.domain.tournament.bracket_entities import ALLOWED_BRACKET_SIZES, BracketNode
from app.domain.tournament.entities import STATUS_COMPLETED, STATUS_DRAFT, STATUS_PUBLISHED


class BracketError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


EDITABLE_MATCH_STATUSES = frozenset({MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED})


def _require_tournament(uow: UnitOfWork, tournament_id: str):
    tournament = uow.tournaments.get(tournament_id)
    if tournament is None:
        raise KeyError(f"tournament not found: {tournament_id}")
    return tournament


def generate_bracket(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    size: int,
    replace: bool = False,
) -> list[BracketNode]:
    tournament = _require_tournament(uow, tournament_id)
    if tournament.status == STATUS_COMPLETED:
        raise BracketError("cannot edit completed tournament", code="frozen")
    if size not in ALLOWED_BRACKET_SIZES:
        raise BracketError(f"size must be one of {sorted(ALLOWED_BRACKET_SIZES)}", code="bad_size")
    if log2(size) != int(log2(size)):
        raise BracketError("size must be power of 2", code="bad_size")

    existing = uow.bracket_nodes.count_for_tournament(tournament_id)
    if existing and not replace:
        raise BracketError("bracket already exists (pass replace=true)", code="exists")
    if existing and replace:
        if tournament.status != STATUS_DRAFT:
            raise BracketError("replace only allowed while draft", code="frozen")
        # refuse replace if any linked match already started
        for node in uow.bracket_nodes.list_for_tournament(tournament_id):
            if node.match_id:
                match = uow.matches.get(node.match_id)
                if match and match.status not in EDITABLE_MATCH_STATUSES:
                    raise BracketError("cannot replace: match already started", code="frozen")
        uow.bracket_nodes.delete_for_tournament(tournament_id)

    rounds = int(log2(size))
    # Build round 0 first, then wire sources upward.
    by_round: dict[int, list[BracketNode]] = {}
    for r in range(rounds):
        count = size // (2 ** (r + 1))
        by_round[r] = []
        for pos in range(count):
            node = BracketNode(
                id=str(uuid4()),
                tournament_id=tournament_id,
                round=r,
                position=pos,
            )
            by_round[r].append(node)

    for r in range(1, rounds):
        for pos, node in enumerate(by_round[r]):
            src_round = by_round[r - 1]
            node.source_a_node_id = src_round[pos * 2].id
            node.source_b_node_id = src_round[pos * 2 + 1].id

    nodes: list[BracketNode] = []
    for r in range(rounds):
        for node in by_round[r]:
            uow.bracket_nodes.add(node)
            nodes.append(node)

    flush = getattr(uow, "flush", None)
    if callable(flush):
        flush()
    uow.commit()
    return nodes


def _assert_team_in_tournament(uow: UnitOfWork, tournament_id: str, team_id: str | None) -> None:
    if team_id is None:
        return
    team = uow.teams.get(team_id)
    if team is None or team.tournament_id != tournament_id:
        raise BracketError(f"team not in tournament: {team_id}", code="bad_team")


def _team_already_assigned(
    uow: UnitOfWork,
    tournament_id: str,
    team_id: str,
    *,
    except_node_id: str,
    only_round: int | None = 0,
) -> bool:
    for node in uow.bracket_nodes.list_for_tournament(tournament_id):
        if node.id == except_node_id:
            continue
        if only_round is not None and node.round != only_round:
            continue
        if node.team_a_id == team_id or node.team_b_id == team_id:
            return True
    return False


def _node_editable(uow: UnitOfWork, tournament_status: str, node: BracketNode) -> None:
    if tournament_status == STATUS_COMPLETED:
        raise BracketError("cannot edit completed tournament", code="frozen")
    if tournament_status == STATUS_PUBLISHED and node.match_id:
        match = uow.matches.get(node.match_id)
        if match and match.status not in EDITABLE_MATCH_STATUSES:
            raise BracketError("match already started", code="frozen")


def _ensure_match_for_node(uow: UnitOfWork, node: BracketNode) -> BracketNode:
    if node.match_id or not node.pair_ready():
        return node
    match = create_match(
        uow,
        tournament_id=node.tournament_id,
        commit=False,
    )
    node.match_id = match.id
    uow.bracket_nodes.save(node)
    flush = getattr(uow, "flush", None)
    if callable(flush):
        flush()
    return node


def assign_bracket_slot(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    node_id: str,
    team_a_id: str | None = None,
    team_b_id: str | None = None,
    clear_team_a: bool = False,
    clear_team_b: bool = False,
) -> BracketNode:
    tournament = _require_tournament(uow, tournament_id)
    node = uow.bracket_nodes.get(node_id)
    if node is None or node.tournament_id != tournament_id:
        raise KeyError(f"bracket node not found: {node_id}")
    _node_editable(uow, tournament.status, node)

    # Round 0: unique seeding. Later rounds: manual winners (may repeat SF teams).
    unique_round = 0 if node.round == 0 else None

    if clear_team_a:
        node.team_a_id = None
    elif team_a_id is not None:
        _assert_team_in_tournament(uow, tournament_id, team_a_id)
        if unique_round is not None and _team_already_assigned(
            uow,
            tournament_id,
            team_a_id,
            except_node_id=node.id,
            only_round=unique_round,
        ):
            raise BracketError("team already placed in first round", code="team_taken")
        node.team_a_id = team_a_id

    if clear_team_b:
        node.team_b_id = None
    elif team_b_id is not None:
        _assert_team_in_tournament(uow, tournament_id, team_b_id)
        if unique_round is not None and _team_already_assigned(
            uow,
            tournament_id,
            team_b_id,
            except_node_id=node.id,
            only_round=unique_round,
        ):
            raise BracketError("team already placed in first round", code="team_taken")
        node.team_b_id = team_b_id

    if node.team_a_id and node.team_b_id and node.team_a_id == node.team_b_id:
        raise BracketError("team_a and team_b must differ", code="same_team")

    uow.bracket_nodes.save(node)
    node = _ensure_match_for_node(uow, node)
    uow.commit()
    return node


def get_bracket_tree(uow: UnitOfWork, *, tournament_id: str) -> list[BracketNode]:
    _require_tournament(uow, tournament_id)
    nodes = uow.bracket_nodes.list_for_tournament(tournament_id)
    return sorted(nodes, key=lambda n: (n.round, n.position))
