"""Normalize inbound webhook JSON → typed fields (no MatchZy types)."""

from __future__ import annotations

from typing import Any


class NormalizeError(ValueError):
    pass


def normalize_cs2_event(body: dict[str, Any]) -> dict[str, Any]:
    required = ("event_id", "sequence", "server_id", "match_id", "type", "timestamp")
    missing = [k for k in required if k not in body or body[k] in (None, "")]
    if missing:
        raise NormalizeError(f"missing fields: {', '.join(missing)}")

    sequence = body["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise NormalizeError("sequence must be int >= 1")

    event_type = body["type"]
    if not isinstance(event_type, str):
        raise NormalizeError("type must be string")

    payload = body.get("payload") or {}
    if not isinstance(payload, dict):
        raise NormalizeError("payload must be object")

    return {
        "event_id": str(body["event_id"]),
        "sequence": sequence,
        "server_id": str(body["server_id"]),
        "match_id": str(body["match_id"]),
        "type": event_type,
        "timestamp": str(body["timestamp"]),
        "correlation_id": (
            str(body["correlation_id"]) if body.get("correlation_id") else None
        ),
        "payload": payload,
    }
