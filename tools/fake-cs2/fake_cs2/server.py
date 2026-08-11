"""HTTP listener: health, snapshot, commands (+ ack)."""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from fake_cs2 import PROTOCOL_VERSION, __version__
from fake_cs2.config import FakeConfig
from fake_cs2.events import EventEmitter
from fake_cs2.state import MatchState, utc_now_iso

logger = logging.getLogger("fake_cs2.server")

COMMAND_TYPES = {
    "LoadMatch",
    "PauseMatch",
    "ResumeMatch",
    "ForfeitMatch",
    "GetSnapshot",
}


class FakeHttpServer:
    def __init__(
        self,
        config: FakeConfig,
        state: MatchState,
        emitter: EventEmitter,
    ) -> None:
        self.config = config
        self.state = state
        self.emitter = emitter
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self, *, background: bool = True) -> None:
        handler = self._make_handler()
        self._httpd = ThreadingHTTPServer(
            (self.config.listen_host, self.config.listen_port),
            handler,
        )
        if background:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever,
                name="fake-cs2-http",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "listening on http://%s:%s",
                self.config.listen_host,
                self.config.listen_port,
            )
        else:
            logger.info(
                "listening (blocking) on http://%s:%s",
                self.config.listen_host,
                self.config.listen_port,
            )
            self._httpd.serve_forever()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                logger.debug("%s - %s", self.address_string(), fmt % args)

            def _send_json(self, code: int, payload: dict[str, Any]) -> None:
                raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path.rstrip("/") or "/"
                if path == "/health":
                    self._send_json(
                        200,
                        {
                            "status": "ok",
                            "role": "fake-cs2",
                            "version": __version__,
                            "protocol_version": PROTOCOL_VERSION,
                            "match_id": outer.state.match_id,
                            "server_id": outer.state.server_id,
                            "last_sequence": outer.state.last_sequence,
                        },
                    )
                    return
                if path == "/v1/snapshot":
                    self._send_json(200, outer.state.snapshot())
                    return
                self._send_json(404, {"error": "not_found", "path": path})

            def do_POST(self) -> None:  # noqa: N802
                path = urlparse(self.path).path.rstrip("/") or "/"
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    self._send_json(400, {"error": "invalid_json"})
                    return

                if path == "/v1/commands":
                    self._handle_command(body)
                    return
                self._send_json(404, {"error": "not_found", "path": path})

            def _handle_command(self, body: dict[str, Any]) -> None:
                command_id = body.get("command_id")
                command_type = body.get("type")
                if not command_id or not isinstance(command_id, str):
                    self._send_json(400, {"error": "command_id required"})
                    return
                if command_type not in COMMAND_TYPES:
                    self._send_json(
                        400,
                        {
                            "error": "unknown_type",
                            "allowed": sorted(COMMAND_TYPES),
                        },
                    )
                    return

                match_id = body.get("match_id")
                if match_id and match_id != outer.state.match_id:
                    self._send_json(
                        409,
                        {
                            "error": "match_id_mismatch",
                            "expected": outer.state.match_id,
                        },
                    )
                    return

                payload = body.get("payload") or {}
                if not isinstance(payload, dict):
                    self._send_json(400, {"error": "payload must be object"})
                    return

                record = outer.state.apply_command(
                    command_id=command_id,
                    command_type=command_type,
                    payload=payload,
                )

                # Side-effect events after confirmed apply (not on duplicate).
                if record.status == "confirmed":
                    outer._emit_after_command(command_type, payload)

                ack = {
                    "command_id": record.command_id,
                    "type": record.type,
                    "status": record.status,
                    "timestamp": record.timestamp or utc_now_iso(),
                    "error": record.error,
                    "result": record.result,
                }
                self._send_json(200, ack)

        return Handler

    def _emit_after_command(
        self, command_type: str, payload: dict[str, Any]
    ) -> None:
        if command_type == "LoadMatch":
            self.emitter.emit(
                "match_loaded",
                {"map": self.state.map_name},
            )
        elif command_type == "PauseMatch":
            self.state.mark_tech_pause(True)
            self.emitter.emit(
                "tech_pause_started",
                {"reason": payload.get("reason", "command")},
            )
        elif command_type == "ResumeMatch":
            self.state.mark_tech_pause(False)
            self.emitter.emit("tech_pause_ended", {})
        elif command_type == "ForfeitMatch":
            snap = self.state.snapshot()
            from fake_cs2.demo_stub import write_ephemeral_demo

            demo_path = write_ephemeral_demo(
                match_id=self.state.match_id,
                map_name=str(snap.get("map") or "de_mirage"),
            )
            self.emitter.emit(
                "match_completed",
                {
                    "score": snap["score"],
                    "reason": "forfeit",
                    "losing_team": payload.get("losing_team"),
                    "demo_path": str(demo_path),
                },
            )
