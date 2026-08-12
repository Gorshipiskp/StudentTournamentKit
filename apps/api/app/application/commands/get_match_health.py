"""Match health aggregate — component statuses (INVARIANTS §14)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.application.commands.rebuild_overlay import seed_overlay_and_production
from app.application.unit_of_work import UnitOfWork
from app.domain.production.entities import (
    AGENT_CONNECTED,
    AGENT_DEGRADED,
    AGENT_DISCONNECTED,
    BROADCAST_IDLE,
    BROADCAST_STREAMING,
    BROADCAST_UNKNOWN,
    OBS_CONNECTED,
    OBS_DISCONNECTED,
)

# Aggregate / component enum — do not invent new names (INVARIANTS §14)
HEALTHY = "HEALTHY"
DEGRADED = "DEGRADED"
OFFLINE = "OFFLINE"
UNKNOWN = "UNKNOWN"

_RANK = {HEALTHY: 0, UNKNOWN: 1, DEGRADED: 2, OFFLINE: 3}

# Overlay snapshot older than this → DEGRADED (still has data)
_OVERLAY_STALE_SECONDS = 120
# Game server heartbeat window
_HEARTBEAT_OK_SECONDS = 90


def get_match_health(uow: UnitOfWork, *, match_id: str) -> dict[str, Any]:
    """
    Aggregate health for director / ops.

    Platform is HEALTHY if this handler can load the match (DB reachable).
    Fake game server (`srv_fake`) is HEALTHY without heartbeat.
    """
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")

    production = uow.production.get(match_id)
    overlay = uow.overlays.get(match_id)
    if production is None or overlay is None:
        seed_overlay_and_production(uow, match)
        production = uow.production.get(match_id)
        overlay = uow.overlays.get(match_id)
    assert production is not None

    now = datetime.now(UTC)
    components: dict[str, dict[str, Any]] = {
        "platform": _component(HEALTHY, detail="api"),
        "agent": _agent_component(production.agent_status),
        "obs": _obs_component(production.obs_status, production.agent_status),
        "overlay": _overlay_component(overlay, now),
        "game_server": _game_server_component(uow, match.game_server_id, now),
        "broadcast": _broadcast_component(production.broadcast_status),
        "whip": _whip_component(match_id),
    }

    # Broadcast / whip stubs must not drag overall down (whip is informational)
    overall_parts = [
        components["platform"]["status"],
        components["agent"]["status"],
        components["obs"]["status"],
        components["overlay"]["status"],
        components["game_server"]["status"],
    ]
    if components["broadcast"]["status"] != UNKNOWN:
        overall_parts.append(components["broadcast"]["status"])

    return {
        "match_id": match_id,
        "overall": _worst(overall_parts),
        "components": components,
        "production": {
            "desired_scene": production.desired_scene,
            "actual_scene": production.actual_scene,
            "agent_status": production.agent_status,
            "obs_status": production.obs_status,
            "broadcast_status": production.broadcast_status,
        },
    }


def _component(status: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"status": status}
    body.update(extra)
    return body


def _worst(statuses: list[str]) -> str:
    return max(statuses, key=lambda s: _RANK.get(s, 1))


def _agent_component(raw: str) -> dict[str, Any]:
    if raw == AGENT_CONNECTED:
        status = HEALTHY
    elif raw == AGENT_DEGRADED:
        status = DEGRADED
    elif raw == AGENT_DISCONNECTED:
        status = OFFLINE
    else:
        status = UNKNOWN
    return _component(status, raw=raw)


def _obs_component(obs_raw: str, agent_raw: str) -> dict[str, Any]:
    if agent_raw == AGENT_DISCONNECTED:
        # Without agent we cannot verify OBS
        return _component(OFFLINE if obs_raw == OBS_DISCONNECTED else UNKNOWN, raw=obs_raw)
    if obs_raw == OBS_CONNECTED:
        return _component(HEALTHY, raw=obs_raw)
    if obs_raw == OBS_DISCONNECTED:
        return _component(OFFLINE, raw=obs_raw)
    return _component(UNKNOWN, raw=obs_raw)


def _overlay_component(overlay: Any, now: datetime) -> dict[str, Any]:
    if overlay is None:
        return _component(OFFLINE, revision=None, age_seconds=None, scene=None)
    age: int | None = None
    if overlay.updated_at is not None:
        ts = overlay.updated_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        age = max(0, int((now - ts).total_seconds()))
    if age is None:
        status = HEALTHY if overlay.revision >= 1 else UNKNOWN
    elif age <= _OVERLAY_STALE_SECONDS:
        status = HEALTHY
    else:
        status = DEGRADED
    return _component(
        status,
        revision=overlay.revision,
        age_seconds=age,
        scene=overlay.scene,
    )


def _game_server_component(
    uow: UnitOfWork,
    game_server_id: str | None,
    now: datetime,
) -> dict[str, Any]:
    if not game_server_id:
        return _component(UNKNOWN, mode="none", id=None, last_heartbeat=None)

    # Fake path (TZ005 / GATE): no live CS2 required
    if game_server_id == "srv_fake" or game_server_id.startswith("srv_fake"):
        return _component(
            HEALTHY,
            mode="fake",
            id=game_server_id,
            last_heartbeat=None,
        )

    server = uow.game_servers.get(game_server_id)
    if server is None:
        return _component(
            DEGRADED,
            mode="unknown",
            id=game_server_id,
            last_heartbeat=None,
            detail="not_in_registry",
        )

    hb = server.last_heartbeat
    hb_iso = hb.isoformat() if hb else None
    if hb is None:
        return _component(
            DEGRADED,
            mode="live",
            id=game_server_id,
            last_heartbeat=None,
            detail="no_heartbeat",
        )
    if hb.tzinfo is None:
        hb = hb.replace(tzinfo=UTC)
    age = int((now - hb).total_seconds())
    if age <= _HEARTBEAT_OK_SECONDS:
        return _component(
            HEALTHY,
            mode="live",
            id=game_server_id,
            last_heartbeat=hb_iso,
            age_seconds=age,
        )
    return _component(
        DEGRADED,
        mode="live",
        id=game_server_id,
        last_heartbeat=hb_iso,
        age_seconds=age,
        detail="stale_heartbeat",
    )


def _broadcast_component(raw: str) -> dict[str, Any]:
    if raw == BROADCAST_STREAMING:
        return _component(HEALTHY, raw=raw)
    if raw == BROADCAST_IDLE:
        return _component(HEALTHY, raw=raw)
    if raw == BROADCAST_UNKNOWN:
        return _component(UNKNOWN, raw=raw)
    return _component(UNKNOWN, raw=raw)


def _whip_component(match_id: str) -> dict[str, Any]:
    """Optional MediaMTX publisher probe (TZ011). Informational; never raises."""
    base = (os.environ.get("MEDIAMTX_API_URL") or "").rstrip("/")
    path = f"stk/{match_id}"
    if not base:
        return _component(UNKNOWN, detail="MEDIAMTX_API_URL unset", path=path)
    url = f"{base}/v3/paths/get/{path}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            body = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return _component(DEGRADED, detail="path missing / no publisher", path=path)
        return _component(UNKNOWN, detail=f"mediamtx http {exc.code}", path=path)
    except Exception as exc:  # noqa: BLE001
        return _component(UNKNOWN, detail=type(exc).__name__, path=path)

    ready = bool(body.get("ready"))
    source = body.get("source") or {}
    if ready and source:
        return _component(
            HEALTHY,
            detail="publisher online",
            path=path,
            source_type=source.get("type"),
            tracks=body.get("tracks"),
        )
    return _component(DEGRADED, detail="waiting publisher", path=path, ready=ready)
