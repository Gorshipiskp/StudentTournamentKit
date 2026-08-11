"""CLI: run / self-test / emit-rounds / simulate."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Sequence

from fake_cs2 import PROTOCOL_VERSION, __version__
from fake_cs2.config import FakeConfig
from fake_cs2.events import EventEmitter
from fake_cs2.hmac_util import sign_body, verify_signature
from fake_cs2.server import FakeHttpServer
from fake_cs2.state import MatchState


def _build(args: argparse.Namespace) -> tuple[FakeConfig, MatchState, EventEmitter]:
    config = FakeConfig.from_env(
        platform_url=getattr(args, "platform_url", None),
        match_id=getattr(args, "match_id", None),
        server_id=getattr(args, "server_id", None),
        webhook_secret=getattr(args, "webhook_secret", None),
        listen_host=getattr(args, "listen_host", None),
        listen_port=getattr(args, "listen_port", None),
        map_name=getattr(args, "map_name", None),
        dry_run=getattr(args, "dry_run", None),
        events_log=getattr(args, "events_log", None),
    )
    state = MatchState(
        match_id=config.match_id,
        server_id=config.server_id,
        map_name=config.map_name,
    )
    emitter = EventEmitter(config, state)
    return config, state, emitter


def cmd_run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config, state, emitter = _build(args)
    server = FakeHttpServer(config, state, emitter)
    print(
        json.dumps(
            {
                "msg": "fake-cs2 starting",
                "listen": f"http://{config.listen_host}:{config.listen_port}",
                "events_url": config.events_url,
                "match_id": config.match_id,
                "server_id": config.server_id,
                "dry_run": config.dry_run,
                "protocol_version": PROTOCOL_VERSION,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    # Auto-load so emit-rounds / external clients can proceed without LoadMatch.
    if not args.no_autoload:
        state.apply_command(
            command_id="autoload-bootstrap",
            command_type="LoadMatch",
            payload={"map": config.map_name},
        )
        emitter.emit("match_loaded", {"map": config.map_name})

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nshutting down", flush=True)
        server.stop()
    return 0


def cmd_emit_rounds(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO)
    config, state, emitter = _build(args)
    if not state.loaded:
        state.apply_command(
            command_id="emit-rounds-load",
            command_type="LoadMatch",
            payload={"map": config.map_name},
        )
        emitter.emit("match_loaded", {"map": config.map_name})

    winners = ["team_a", "team_b"]
    for i in range(args.count):
        start = state.start_round(phase="buy")
        emitter.emit("round_start", start)
        time.sleep(args.delay)
        # Live phase signal (optional clarity for judge arm on buy → live)
        state.phase = "live"
        end = state.end_round(winner=winners[i % 2])
        result = emitter.emit("round_end", end)
        print(
            json.dumps(
                {
                    "round": end["round"],
                    "score": end["score"],
                    "http_status": result.http_status,
                    "error": result.error,
                    "events_url": config.events_url,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(args.delay)
    print(json.dumps({"snapshot": state.snapshot()}, ensure_ascii=False), flush=True)
    return 0


def cmd_self_test(args: argparse.Namespace) -> int:
    """In-process smoke: state machine + HMAC + command idempotency (no Platform)."""
    logging.basicConfig(level=logging.WARNING)
    config = FakeConfig.from_env(
        dry_run=True,
        events_log=None,
        match_id="m_selftest",
        server_id="srv_selftest",
        webhook_secret="selftest_secret",
        listen_port=0,  # unused
    )
    state = MatchState(
        match_id=config.match_id,
        server_id=config.server_id,
        map_name=config.map_name,
    )
    emitter = EventEmitter(config, state)

    # HMAC
    body = b'{"event_id":"x"}'
    sig = sign_body(config.webhook_secret, body)
    assert sig.startswith("sha256=")
    assert verify_signature(config.webhook_secret, body, sig)
    assert not verify_signature("wrong", body, sig)

    # Load
    ack = state.apply_command(
        command_id="cmd-load-1",
        command_type="LoadMatch",
        payload={"map": "de_dust2"},
    )
    assert ack.status == "confirmed"
    assert state.loaded and state.map_name == "de_dust2"

    # Idempotent command_id
    ack2 = state.apply_command(
        command_id="cmd-load-1",
        command_type="LoadMatch",
        payload={"map": "de_mirage"},
    )
    assert ack2.status == "duplicate"
    assert state.map_name == "de_dust2"

    # Rounds + events (dry-run)
    r1 = state.start_round(phase="buy")
    e1 = emitter.emit("round_start", r1)
    assert e1.event["sequence"] == 1
    assert e1.dry_run
    end1 = state.end_round(winner="team_a")
    e2 = emitter.emit("round_end", end1)
    assert e2.event["sequence"] == 2
    assert state.score_a == 1

    # Pause / resume
    p = state.apply_command(command_id="cmd-pause", command_type="PauseMatch")
    assert p.status == "confirmed" and state.paused
    try:
        state.start_round()
        raise AssertionError("expected pause block")
    except ValueError:
        pass
    r = state.apply_command(command_id="cmd-resume", command_type="ResumeMatch")
    assert r.status == "confirmed" and not state.paused

    # Snapshot
    snap_ack = state.apply_command(
        command_id="cmd-snap", command_type="GetSnapshot"
    )
    assert snap_ack.status == "confirmed"
    assert snap_ack.result is not None
    snap = snap_ack.result["snapshot"]
    assert snap["score"]["team_a"] == 1
    assert snap["last_sequence"] == 2

    # Forfeit
    f = state.apply_command(
        command_id="cmd-ff",
        command_type="ForfeitMatch",
        payload={"losing_team": "team_b"},
    )
    assert f.status == "confirmed"
    assert state.completed and state.phase == "ended"
    assert state.score_a >= 13

    # HTTP server smoke (health + command)
    config_srv = FakeConfig.from_env(
        dry_run=True,
        listen_host="127.0.0.1",
        listen_port=27198,
        match_id="m_http",
        server_id="srv_http",
        webhook_secret="http_secret",
    )
    state_srv = MatchState(
        match_id=config_srv.match_id,
        server_id=config_srv.server_id,
        map_name="de_mirage",
    )
    emitter_srv = EventEmitter(config_srv, state_srv)
    server = FakeHttpServer(config_srv, state_srv, emitter_srv)
    server.start(background=True)
    try:
        import urllib.request

        with urllib.request.urlopen(
            f"http://{config_srv.listen_host}:{config_srv.listen_port}/health",
            timeout=2,
        ) as resp:
            health = json.loads(resp.read().decode())
            assert health["status"] == "ok"
            assert health["protocol_version"] == PROTOCOL_VERSION

        cmd_body = json.dumps(
            {
                "command_id": "http-load",
                "type": "LoadMatch",
                "match_id": config_srv.match_id,
                "payload": {"map": "de_inferno"},
            }
        ).encode()
        req = urllib.request.Request(
            f"http://{config_srv.listen_host}:{config_srv.listen_port}/v1/commands",
            data=cmd_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            ack_http = json.loads(resp.read().decode())
            assert ack_http["status"] == "confirmed"

        with urllib.request.urlopen(
            f"http://{config_srv.listen_host}:{config_srv.listen_port}/v1/snapshot",
            timeout=2,
        ) as resp:
            snap_http = json.loads(resp.read().decode())
            assert snap_http["map"] == "de_inferno"
            assert snap_http["loaded"] is True
    finally:
        server.stop()

    print(
        json.dumps(
            {
                "self_test": "ok",
                "version": __version__,
                "protocol_version": PROTOCOL_VERSION,
                "events_url_template": FakeConfig.from_env().events_url,
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_finalize_demo(args: argparse.Namespace) -> int:
    """Write ephemeral Fake demo and emit match_completed (Platform durable copy)."""
    from fake_cs2.demo_stub import write_ephemeral_demo

    logging.basicConfig(level=logging.INFO)
    config, state, emitter = _build(args)
    if not state.loaded:
        state.apply_command(
            command_id="finalize-load",
            command_type="LoadMatch",
            payload={"map": config.map_name},
        )
    state.completed = True
    state.phase = "ended"
    demo_path = write_ephemeral_demo(
        match_id=config.match_id,
        map_name=config.map_name,
        directory=args.demo_dir,
    )
    result = emitter.emit(
        "match_completed",
        {
            "score": {"team_a": state.score_a, "team_b": state.score_b},
            "reason": "normal",
            "demo_path": str(demo_path),
        },
    )
    print(
        json.dumps(
            {
                "ephemeral_demo": str(demo_path),
                "events_url": config.events_url,
                "http_status": result.http_status,
                "error": result.error,
                "dry_run": result.dry_run,
                "note": "Platform should copy to data/demos/{match_id}/ and set demo_files.durable_uri",
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_post_probe(args: argparse.Namespace) -> int:
    """Single POST to Platform events URL (may 404 until P2) — proves wiring."""
    logging.basicConfig(level=logging.INFO)
    config, state, emitter = _build(args)
    state.apply_command(
        command_id="probe-load",
        command_type="LoadMatch",
        payload={"map": config.map_name},
    )
    result = emitter.emit(
        "heartbeat",
        {
            "bridge_version": f"fake-cs2/{__version__}",
            "protocol_version": PROTOCOL_VERSION,
        },
    )
    out = {
        "events_url": config.events_url,
        "http_status": result.http_status,
        "error": result.error,
        "dry_run": result.dry_run,
        "event_id": result.event["event_id"],
        "sequence": result.event["sequence"],
        "note": (
            "404/connection error OK until Platform ingest (TZ002 P2); "
            "URL and HMAC headers are the contract."
        ),
    }
    print(json.dumps(out, ensure_ascii=False))
    # Exit 0 even on 404 — probe is informational for P1.
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fake-cs2",
        description="Fake CS2 game server for STP (events + commands + snapshot)",
    )
    p.add_argument("--version", action="version", version=f"fake-cs2 {__version__}")
    p.add_argument("-v", "--verbose", action="store_true")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--platform-url",
        default=None,
        help="Platform base URL (default env FAKE_CS2_PLATFORM_URL or http://127.0.0.1:8000)",
    )
    common.add_argument("--match-id", default=None)
    common.add_argument("--server-id", default=None)
    common.add_argument("--webhook-secret", default=None)
    common.add_argument("--listen-host", default=None)
    common.add_argument("--listen-port", type=int, default=None)
    common.add_argument("--map-name", default=None)
    common.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Print events to stdout instead of POST",
    )
    common.add_argument(
        "--events-log",
        default=None,
        help="Append each event JSON line to this file",
    )

    sub = p.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", parents=[common], help="Start HTTP listener")
    run_p.add_argument(
        "--no-autoload",
        action="store_true",
        help="Do not LoadMatch on startup",
    )
    run_p.set_defaults(func=cmd_run)

    emit_p = sub.add_parser(
        "emit-rounds",
        parents=[common],
        help="Simulate N rounds (POST or dry-run)",
    )
    emit_p.add_argument("--count", type=int, default=2)
    emit_p.add_argument("--delay", type=float, default=0.05)
    emit_p.set_defaults(func=cmd_emit_rounds)

    st = sub.add_parser("self-test", help="In-process smoke (no Platform required)")
    st.set_defaults(func=cmd_self_test)

    probe = sub.add_parser(
        "post-probe",
        parents=[common],
        help="One POST to /api/v1/internal/cs2/events (404 OK until P2)",
    )
    probe.set_defaults(func=cmd_post_probe)

    fin = sub.add_parser(
        "finalize-demo",
        parents=[common],
        help="Write ephemeral .dem stub + emit match_completed (durable copy on Platform)",
    )
    fin.add_argument(
        "--demo-dir",
        default=None,
        help="Directory for ephemeral demo (default data/demos/_ephemeral/<match_id>)",
    )
    fin.set_defaults(func=cmd_finalize_demo)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
