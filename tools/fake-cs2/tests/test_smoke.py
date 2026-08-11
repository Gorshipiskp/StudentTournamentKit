"""Pytest smoke for Fake Game Server (self-check)."""

from __future__ import annotations

import json
import urllib.request

from fake_cs2 import PROTOCOL_VERSION
from fake_cs2.cli import cmd_self_test
from fake_cs2.config import FakeConfig
from fake_cs2.events import EventEmitter
from fake_cs2.hmac_util import sign_body
from fake_cs2.server import FakeHttpServer
from fake_cs2.state import MatchState


def test_cli_self_test_exits_zero() -> None:
    class Args:
        pass

    assert cmd_self_test(Args()) == 0


def test_event_url_and_hmac_headers_shape() -> None:
    config = FakeConfig(
        platform_url="http://127.0.0.1:8000",
        match_id="m1",
        server_id="s1",
        webhook_secret="secret",
        dry_run=True,
    )
    assert config.events_url == "http://127.0.0.1:8000/api/v1/internal/cs2/events"
    state = MatchState(match_id="m1", server_id="s1")
    state.apply_command(
        command_id="c1", command_type="LoadMatch", payload={"map": "de_mirage"}
    )
    emitter = EventEmitter(config, state)
    event = emitter.build_event("round_start", {"round": 1, "phase": "buy"})
    raw = json.dumps(event, separators=(",", ":")).encode()
    sig = sign_body("secret", raw)
    assert sig.startswith("sha256=")
    assert len(sig) == len("sha256=") + 64


def test_pause_resume_forfeit_and_snapshot_http() -> None:
    config = FakeConfig(
        platform_url="http://127.0.0.1:8000",
        match_id="m_http",
        server_id="s_http",
        webhook_secret="sec",
        listen_host="127.0.0.1",
        listen_port=27197,
        dry_run=True,
    )
    state = MatchState(match_id=config.match_id, server_id=config.server_id)
    emitter = EventEmitter(config, state)
    server = FakeHttpServer(config, state, emitter)
    server.start(background=True)
    try:
        base = f"http://{config.listen_host}:{config.listen_port}"

        def post_cmd(payload: dict) -> dict:
            raw = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{base}/v1/commands",
                data=raw,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return json.loads(resp.read().decode())

        assert post_cmd(
            {
                "command_id": "1",
                "type": "LoadMatch",
                "match_id": config.match_id,
                "payload": {"map": "de_nuke"},
            }
        )["status"] == "confirmed"
        assert post_cmd({"command_id": "2", "type": "PauseMatch"})["status"] == "confirmed"
        assert state.paused
        assert post_cmd({"command_id": "3", "type": "ResumeMatch"})["status"] == "confirmed"
        snap = post_cmd({"command_id": "4", "type": "GetSnapshot"})
        assert snap["status"] == "confirmed"
        assert snap["result"]["snapshot"]["map"] == "de_nuke"
        ff = post_cmd(
            {
                "command_id": "5",
                "type": "ForfeitMatch",
                "payload": {"losing_team": "team_a"},
            }
        )
        assert ff["status"] == "confirmed"
        assert state.completed

        with urllib.request.urlopen(f"{base}/health", timeout=2) as resp:
            health = json.loads(resp.read().decode())
        assert health["protocol_version"] == PROTOCOL_VERSION
    finally:
        server.stop()
