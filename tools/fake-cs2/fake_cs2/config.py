"""Config for Fake Game Server (env + CLI overrides)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FakeConfig:
    platform_url: str
    match_id: str
    server_id: str
    webhook_secret: str
    listen_host: str = "127.0.0.1"
    listen_port: int = 27099
    map_name: str = "de_mirage"
    dry_run: bool = False
    events_log: str | None = None

    @property
    def events_url(self) -> str:
        base = self.platform_url.rstrip("/")
        return f"{base}/api/v1/internal/cs2/events"

    @classmethod
    def from_env(cls, **overrides: object) -> FakeConfig:
        def _bool(name: str, default: bool) -> bool:
            raw = os.environ.get(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        data = {
            "platform_url": os.environ.get(
                "FAKE_CS2_PLATFORM_URL", "http://127.0.0.1:8000"
            ),
            "match_id": os.environ.get("FAKE_CS2_MATCH_ID", "m_dev"),
            "server_id": os.environ.get("FAKE_CS2_SERVER_ID", "srv_fake"),
            "webhook_secret": os.environ.get(
                "FAKE_CS2_WEBHOOK_SECRET", "dev_webhook_secret_change_me"
            ),
            "listen_host": os.environ.get("FAKE_CS2_LISTEN_HOST", "127.0.0.1"),
            "listen_port": int(os.environ.get("FAKE_CS2_LISTEN_PORT", "27099")),
            "map_name": os.environ.get("FAKE_CS2_MAP", "de_mirage"),
            "dry_run": _bool("FAKE_CS2_DRY_RUN", False),
            "events_log": os.environ.get("FAKE_CS2_EVENTS_LOG") or None,
        }
        data.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**data)  # type: ignore[arg-type]
