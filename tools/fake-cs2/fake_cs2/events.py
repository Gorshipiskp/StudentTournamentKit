"""Emit normalized events to Platform (or dry-run / log file)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fake_cs2 import PROTOCOL_VERSION
from fake_cs2.config import FakeConfig
from fake_cs2.hmac_util import sign_body
from fake_cs2.state import MatchState, utc_now_iso

logger = logging.getLogger("fake_cs2.events")


@dataclass
class EmitResult:
    event: dict[str, Any]
    http_status: int | None
    body: str | None
    dry_run: bool
    error: str | None = None


class EventEmitter:
    def __init__(self, config: FakeConfig, state: MatchState) -> None:
        self.config = config
        self.state = state

    def build_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        seq = self.state.next_sequence()
        event = {
            "event_id": event_id or MatchState.new_event_id(),
            "sequence": seq,
            "server_id": self.config.server_id,
            "match_id": self.config.match_id,
            "type": event_type,
            "timestamp": utc_now_iso(),
            "correlation_id": correlation_id,
            "payload": payload,
        }
        return event

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
        event_id: str | None = None,
    ) -> EmitResult:
        event = self.build_event(
            event_type,
            payload,
            correlation_id=correlation_id,
            event_id=event_id,
        )
        raw = json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        self._append_log(raw)

        if self.config.dry_run:
            logger.info("dry_run event type=%s sequence=%s", event_type, event["sequence"])
            print(raw.decode("utf-8"), flush=True)
            return EmitResult(
                event=event, http_status=None, body=None, dry_run=True
            )

        headers = {
            "Content-Type": "application/json",
            "X-STP-Signature": sign_body(self.config.webhook_secret, raw),
            "X-STP-Event-Id": event["event_id"],
            "X-STP-Protocol-Version": PROTOCOL_VERSION,
        }
        req = urllib.request.Request(
            self.config.events_url,
            data=raw,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                logger.info(
                    "posted event type=%s sequence=%s status=%s",
                    event_type,
                    event["sequence"],
                    resp.status,
                )
                return EmitResult(
                    event=event,
                    http_status=resp.status,
                    body=body,
                    dry_run=False,
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.warning(
                "POST %s → HTTP %s (expected until Platform ingest P2): %s",
                self.config.events_url,
                exc.code,
                body[:200],
            )
            return EmitResult(
                event=event,
                http_status=exc.code,
                body=body,
                dry_run=False,
                error=f"HTTP {exc.code}",
            )
        except urllib.error.URLError as exc:
            logger.warning(
                "POST %s failed (platform down?): %s",
                self.config.events_url,
                exc.reason,
            )
            return EmitResult(
                event=event,
                http_status=None,
                body=None,
                dry_run=False,
                error=str(exc.reason),
            )

    def _append_log(self, raw: bytes) -> None:
        if not self.config.events_log:
            return
        path = Path(self.config.events_log)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as fh:
            fh.write(raw + b"\n")
