"""Integration: probe against compose MySQL (skip if DB down)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.infrastructure.persistence import models
from app.infrastructure.persistence.db import check_database, reset_engine_cache
from app.infrastructure.persistence.session import get_session_factory, reset_session_factory_cache
from app.main import app


def _configure_host_mysql() -> None:
    os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
    os.environ.setdefault("MYSQL_PORT", "3307")
    os.environ.setdefault("MYSQL_USER", "stp")
    os.environ.setdefault("MYSQL_PASSWORD", "changeme_stp_dev")
    os.environ.setdefault("MYSQL_DATABASE", "stp")
    reset_engine_cache()
    reset_session_factory_cache()


@pytest.fixture(scope="module")
def mysql_ready() -> None:
    _configure_host_mysql()
    if not check_database():
        pytest.skip("MySQL not reachable (start infra/platform compose)")


def test_probe_writes_outbox_and_dispatches(mysql_ready: None) -> None:
    client = TestClient(app)
    response = client.post(
        "/internal/foundation/probe",
        headers={"X-Request-ID": "probe-corr-42"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"] == "probe-corr-42"
    assert body["dispatched"] >= 1
    assert response.headers["X-Request-ID"] == "probe-corr-42"

    session = get_session_factory()()
    try:
        outbox = session.get(models.EventOutbox, body["outbox_id"])
        assert outbox is not None
        assert outbox.correlation_id == "probe-corr-42"
        assert outbox.processed_at is not None
        tournament = session.get(models.Tournament, body["tournament_id"])
        assert tournament is not None
        assert tournament.status == "draft"
    finally:
        session.close()


def test_startup_replay_drains_unprocessed(mysql_ready: None) -> None:
    from uuid import uuid4

    from app.infrastructure.outbox.dispatcher import dispatch_pending

    tournament_id = str(uuid4())
    outbox_id = str(uuid4())
    session = get_session_factory()()
    try:
        session.add(models.Tournament(id=tournament_id, status="draft"))
        session.add(
            models.EventOutbox(
                id=outbox_id,
                event_type="tournament.draft_created",
                aggregate_type="tournament",
                aggregate_id=tournament_id,
                payload={"tournament_id": tournament_id},
                correlation_id="replay-corr",
                processed_at=None,
            )
        )
        session.commit()
    finally:
        session.close()

    processed = dispatch_pending()
    assert processed >= 1

    session = get_session_factory()()
    try:
        row = session.get(models.EventOutbox, outbox_id)
        assert row is not None
        assert row.processed_at is not None
        leftover = session.scalars(
            select(models.EventOutbox).where(models.EventOutbox.processed_at.is_(None))
        ).all()
        # may be empty or only races from other tests; our row must be done
        assert outbox_id not in {r.id for r in leftover}
    finally:
        session.close()
