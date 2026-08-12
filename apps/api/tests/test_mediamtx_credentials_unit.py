"""Unit: MediaMTX WHIP/WHEP credentials + WHEP cap registry."""

from __future__ import annotations

import time

import pytest

from app.infrastructure.realtime.whep_sessions import WhepSessionRegistry
from app.infrastructure.security.mediamtx_credentials import (
    issue_mediamtx_bearer,
    mediamtx_path,
    parse_mediamtx_bearer,
    public_credential_response,
    whep_url,
    whip_url,
)


def test_issue_whip_shape() -> None:
    issued = issue_mediamtx_bearer(
        match_id="m_a",
        action="publish",
        secret="test_secret",
        ttl=120,
        now=1_700_000_000.0,
    )
    assert issued["path"] == "stk/m_a"
    assert issued["whip_url"] == whip_url("m_a")
    assert "whep_url" not in issued
    assert issued["ttl"] == 120
    assert issued["bearer"].startswith("mtx.")
    assert "jti" in issued
    pub = public_credential_response(issued)
    assert "jti" not in pub
    assert "bearer" in pub


def test_issue_whep_and_parse() -> None:
    issued = issue_mediamtx_bearer(
        match_id="m_b",
        action="read",
        secret="test_secret",
        ttl=90,
        now=1_700_000_000.0,
        jti="abc123",
    )
    assert issued["whep_url"].endswith("/stk/m_b/whep")
    claims = parse_mediamtx_bearer(
        issued["bearer"], secret="test_secret", now=1_700_000_000.0
    )
    assert claims["act"] == "read"
    assert claims["path"] == mediamtx_path("m_b")
    assert claims["jti"] == "abc123"


def test_bearer_rejects_tamper_and_expiry() -> None:
    issued = issue_mediamtx_bearer(
        match_id="m_c",
        action="publish",
        secret="test_secret",
        ttl=60,
        now=1000.0,
    )
    with pytest.raises(ValueError):
        parse_mediamtx_bearer(issued["bearer"] + "x", secret="test_secret", now=1000.0)
    with pytest.raises(ValueError):
        parse_mediamtx_bearer(issued["bearer"], secret="test_secret", now=1100.0)


def test_whep_registry_max_two() -> None:
    reg = WhepSessionRegistry(max_per_match=2)
    now = time.time()
    assert reg.try_acquire(
        "m1", jti="a", expires_at=now + 100, invite_id="inv1", now=now
    )
    assert reg.try_acquire(
        "m1", jti="b", expires_at=now + 100, invite_id="inv2", now=now
    )
    assert not reg.try_acquire(
        "m1", jti="c", expires_at=now + 100, invite_id="inv3", now=now
    )
    assert reg.active_count("m1", now=now) == 2
    # same invite refresh replaces slot
    assert reg.try_acquire(
        "m1", jti="a2", expires_at=now + 100, invite_id="inv1", now=now
    )
    assert reg.active_count("m1", now=now) == 2
    # other match independent
    assert reg.try_acquire(
        "m2", jti="d", expires_at=now + 100, invite_id="inv9", now=now
    )
    # expiry frees slot
    assert not reg.try_acquire(
        "m1", jti="e", expires_at=now + 100, invite_id="inv3", now=now
    )
    assert reg.try_acquire(
        "m1", jti="e", expires_at=now + 200, invite_id="inv3", now=now + 150
    )


def test_whep_registry_refresh_same_invite() -> None:
    reg = WhepSessionRegistry(max_per_match=2)
    now = time.time()
    assert reg.try_acquire(
        "m1", jti="1", expires_at=now + 100, invite_id="same", now=now
    )
    assert reg.try_acquire(
        "m1", jti="2", expires_at=now + 100, invite_id="same", now=now
    )
    assert reg.try_acquire(
        "m1", jti="3", expires_at=now + 100, invite_id="same", now=now
    )
    assert reg.active_count("m1", now=now) == 1


def test_urls_strip_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDIAMTX_PUBLIC_URL", "http://media.example/")
    assert whip_url("m_x") == "http://media.example/stk/m_x/whip"
    assert whep_url("m_x") == "http://media.example/stk/m_x/whep"
