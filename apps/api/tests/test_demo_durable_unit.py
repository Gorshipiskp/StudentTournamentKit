"""Durable demo finalize stub (ADR-034)."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from app.application.commands.create_match import create_match
from app.application.commands.finalize_demo import durable_root, finalize_match_demo
from app.application.commands.ingest_cs2_event import ingest_cs2_event
from tests.fakes import InMemoryUnitOfWork


def test_finalize_creates_durable_file_and_row(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEMO_DURABLE_ROOT", str(tmp_path / "demos"))
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_demo", map_name="de_mirage")

    ephemeral = tmp_path / "ephemeral.dem"
    ephemeral.write_bytes(b"FAKE_BYTES")

    demo = finalize_match_demo(
        uow,
        match_id="m_demo",
        source_path=str(ephemeral),
        map_name="de_mirage",
    )
    uow.commit()
    assert demo.size_bytes == len(b"FAKE_BYTES")
    assert "m_demo" in demo.durable_uri
    dest = durable_root() / "m_demo"
    files = list(dest.glob("*.dem"))
    assert len(files) == 1
    assert files[0].read_bytes() == b"FAKE_BYTES"
    assert uow.demos.list_for_match("m_demo")


def test_match_completed_ingest_finalizes_stub(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DEMO_DURABLE_ROOT", str(tmp_path / "demos"))
    uow = InMemoryUnitOfWork()
    create_match(uow, match_id="m_done", game_server_id="srv", map_name="de_nuke")
    out = ingest_cs2_event(
        uow,
        event_id=str(uuid4()),
        sequence=1,
        server_id="srv",
        match_id="m_done",
        event_type="match_completed",
        payload={"score": {"team_a": 13, "team_b": 7}, "reason": "normal"},
    )
    uow.commit()
    assert out["applied"] is True
    assert "demo" in out
    assert out["match"]["status"] == "completed"
    uri = out["demo"]["durable_uri"]
    # File exists under durable root
    root = Path(os.environ["DEMO_DURABLE_ROOT"])
    found = list(root.rglob("*.dem"))
    assert found
    assert found[0].is_file()
    assert out["demo"]["size_bytes"] > 0
    assert "m_done" in uri or found[0].parent.name == "m_done"
