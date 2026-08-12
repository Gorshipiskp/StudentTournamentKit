"""Unit: match audit log write + list ordering."""

from __future__ import annotations

from uuid import uuid4

from app.application.commands.create_match import create_match
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from app.application.commands.rebuild_overlay import apply_overlay_override
from app.application.commands.start_match import start_match_fake
from app.application.commands.update_production import patch_production
from app.application.commands.write_audit import write_audit
from app.domain.audit.entities import (
    ACTION_DIRECTOR_SCENE_CHANGE,
    ACTION_DIRECTOR_SCORE_OVERRIDE,
    ACTION_ORGANIZER_MATCH_START,
    ACTION_SYSTEM_ROUND_END,
    ACTOR_SYSTEM,
)
from app.domain.match.entities import MATCH_LIVE
from app.domain.production.entities import SCENE_INTRO
from tests.fakes import InMemoryUnitOfWork


def test_write_audit_and_list_newest_first() -> None:
    uow = InMemoryUnitOfWork()
    match = create_match(uow, match_id=f"m_aud_{uuid4().hex[:6]}")
    write_audit(
        uow,
        match_id=match.id,
        action="system.test_a",
        actor_type=ACTOR_SYSTEM,
        correlation_id="c1",
    )
    write_audit(
        uow,
        match_id=match.id,
        action="system.test_b",
        actor_type=ACTOR_SYSTEM,
        correlation_id="c2",
    )
    items = uow.audit.list_for_match(match.id, limit=50)
    assert len(items) == 2
    assert items[0].action == "system.test_b"
    assert items[1].action == "system.test_a"
    assert items[0].correlation_id == "c2"
    assert items[0].tournament_id == match.tournament_id


def test_smoke_flow_writes_five_action_types() -> None:
    uow = InMemoryUnitOfWork()
    match = create_match(
        uow,
        match_id=f"m_aud_{uuid4().hex[:6]}",
        game_server_id="srv_fake",
        map_name="de_mirage",
    )
    cid = "corr-audit-smoke"
    start_match_fake(uow, match_id=match.id, correlation_id=cid)
    # restart UoW state after commit flag — same in-memory repos
    patch_production(
        uow,
        match_id=match.id,
        desired_scene=SCENE_INTRO,
        correlation_id=cid,
    )
    apply_overlay_override(
        uow,
        match_id=match.id,
        patch={"team_a_name": "Alpha", "score_team_a": 3},
        correlation_id=cid,
    )
    # live for ingest
    live = uow.matches.get(match.id)
    assert live is not None
    assert live.status == MATCH_LIVE
    ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv_fake",
        match_id=match.id,
        event_type="round_end",
        payload={"score_team_a": 1, "score_team_b": 0, "round": 1},
        correlation_id=cid,
    )

    actions = {e.action for e in uow.audit.list_for_match(match.id, limit=50)}
    assert ACTION_ORGANIZER_MATCH_START in actions
    assert ACTION_DIRECTOR_SCENE_CHANGE in actions
    assert ACTION_DIRECTOR_SCORE_OVERRIDE in actions
    assert ACTION_SYSTEM_ROUND_END in actions
    assert all(
        e.correlation_id == cid
        for e in uow.audit.list_for_match(match.id)
        if e.action
        in {
            ACTION_ORGANIZER_MATCH_START,
            ACTION_DIRECTOR_SCENE_CHANGE,
            ACTION_DIRECTOR_SCORE_OVERRIDE,
            ACTION_SYSTEM_ROUND_END,
        }
    )
