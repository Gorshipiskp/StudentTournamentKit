"""Finalize match demo into durable local storage (ADR-034 stub)."""

from __future__ import annotations

import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.demo.entities import DemoFile


def resolve_repo_root() -> Path:
    """Best-effort: apps/api cwd → repo root; else cwd."""
    cwd = Path.cwd().resolve()
    if (cwd / "data" / "demos").exists() or (cwd / "AGENTS.md").exists():
        return cwd
    if (cwd.parent.parent / "AGENTS.md").exists():
        return cwd.parent.parent
    return cwd


def durable_root() -> Path:
    raw = os.environ.get("DEMO_DURABLE_ROOT")
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = resolve_repo_root() / path
    else:
        path = resolve_repo_root() / "data" / "demos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def finalize_match_demo(
    uow: UnitOfWork,
    *,
    match_id: str,
    source_path: str | None = None,
    map_name: str | None = None,
) -> DemoFile:
    """Copy or create stub .dem under durable root; persist demo_files row."""
    root = durable_root()
    dest_dir = root / match_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_map = (map_name or "map").replace("/", "_").replace("\\", "_")
    dest = dest_dir / f"{safe_map}_{stamp}.dem"

    src = Path(source_path) if source_path else None
    if src is not None and src.is_file():
        shutil.copy2(src, dest)
        source_uri = str(src.resolve())
    else:
        dest.write_bytes(
            b"STP_FAKE_DEMO\n"
            + f"match_id={match_id}\n".encode()
            + f"created={stamp}\n".encode()
        )
        source_uri = None

    # Portable URI relative to repo when possible
    repo = resolve_repo_root()
    try:
        durable_uri = str(dest.resolve().relative_to(repo)).replace("\\", "/")
    except ValueError:
        durable_uri = str(dest.resolve())

    demo = DemoFile(
        id=str(uuid4()),
        match_id=match_id,
        durable_uri=durable_uri,
        size_bytes=dest.stat().st_size,
        map_name=map_name,
        source_uri=source_uri,
        created_at=datetime.now(UTC),
    )
    uow.demos.add(demo)
    return demo
