"""HTTP client: Platform → Fake/Bridge commands (no RCON)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger("stp.cs2.commands")


@dataclass(frozen=True)
class CommandAck:
    http_status: int | None
    ack_status: str | None
    error: str | None
    result: dict[str, Any] | None
    raw_body: str | None = None


class GameCommandTransport(Protocol):
    def send(
        self,
        *,
        endpoint_base: str,
        command_id: str,
        command_type: str,
        match_id: str,
        server_id: str | None,
        payload: dict[str, Any],
        correlation_id: str | None,
    ) -> CommandAck: ...


class HttpGameCommandTransport:
    """POST {endpoint}/v1/commands — CONTRACT §4."""

    def __init__(self, *, timeout_sec: float = 5.0) -> None:
        self.timeout_sec = timeout_sec

    def send(
        self,
        *,
        endpoint_base: str,
        command_id: str,
        command_type: str,
        match_id: str,
        server_id: str | None,
        payload: dict[str, Any],
        correlation_id: str | None,
    ) -> CommandAck:
        base = endpoint_base.rstrip("/")
        url = f"{base}/v1/commands"
        body = {
            "command_id": command_id,
            "type": command_type,
            "match_id": match_id,
            "server_id": server_id,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "correlation_id": correlation_id,
            "payload": payload,
        }
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                return _parse_ack(resp.status, text)
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            logger.warning("command HTTP %s: %s", exc.code, text[:200])
            parsed = _parse_ack(exc.code, text)
            if parsed.ack_status is None:
                return CommandAck(
                    http_status=exc.code,
                    ack_status="failed",
                    error=f"HTTP {exc.code}",
                    result=None,
                    raw_body=text,
                )
            return parsed
        except urllib.error.URLError as exc:
            logger.warning("command URL error: %s", exc.reason)
            return CommandAck(
                http_status=None,
                ack_status="failed",
                error=str(exc.reason),
                result=None,
            )


def _parse_ack(http_status: int, text: str) -> CommandAck:
    try:
        data = json.loads(text or "{}")
    except json.JSONDecodeError:
        return CommandAck(
            http_status=http_status,
            ack_status="failed",
            error="invalid ack JSON",
            result=None,
            raw_body=text,
        )
    if not isinstance(data, dict):
        return CommandAck(
            http_status=http_status,
            ack_status="failed",
            error="ack not object",
            result=None,
            raw_body=text,
        )
    status = data.get("status")
    if not isinstance(status, str):
        status = "failed" if http_status >= 400 else None
    result = data.get("result")
    if result is not None and not isinstance(result, dict):
        result = {"value": result}
    return CommandAck(
        http_status=http_status,
        ack_status=status,
        error=data.get("error") if isinstance(data.get("error"), str) else None,
        result=result,
        raw_body=text,
    )
