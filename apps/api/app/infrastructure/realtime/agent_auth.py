"""Agent token stub (env) — not for production secrets storage."""

from __future__ import annotations

import os


DEFAULT_DEV_TOKEN = "dev_agent_token_change_me"


def resolve_agent_token() -> str:
    return os.environ.get("STK_AGENT_TOKEN") or DEFAULT_DEV_TOKEN


def verify_agent_token(provided: str | None) -> bool:
    if not provided:
        return False
    return provided == resolve_agent_token()
