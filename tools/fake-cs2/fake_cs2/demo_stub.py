"""Write ephemeral Fake GOTV stub (before Platform durable copy)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def write_ephemeral_demo(
    *,
    match_id: str,
    map_name: str = "de_mirage",
    directory: str | Path | None = None,
) -> Path:
    root = Path(directory) if directory else Path("data") / "demos" / "_ephemeral" / match_id
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{map_name}_{stamp}.dem"
    path.write_bytes(
        b"FAKE_CS2_EPHEMERAL_DEMO\n"
        + f"match_id={match_id}\n".encode()
        + f"map={map_name}\n".encode()
    )
    return path.resolve()
