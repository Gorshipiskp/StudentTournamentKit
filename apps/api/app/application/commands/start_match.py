"""Fake / live match start (organizer)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.application.commands.rebuild_overlay import rebuild_overlay_snapshot
from app.application.commands.update_production import patch_production
from app.application.commands.write_audit import write_audit
from app.application.unit_of_work import UnitOfWork
from app.domain.audit.entities import ACTION_ORGANIZER_MATCH_START, ACTOR_ORGANIZER
from app.domain.match.entities import (
    MATCH_CANCELLED,
    MATCH_COMPLETED,
    MATCH_FORFEITED,
    MATCH_LIVE,
    MATCH_SCHEDULED,
    MATCH_SERVER_ASSIGNED,
    MATCH_WARMUP,
)
from app.domain.match.game_command import TYPE_LOAD
from app.domain.production.entities import SCENE_INGAME
from app.infrastructure.adapters.cs2.command_client import (
    GameCommandTransport,
    HttpGameCommandTransport,
)

_TERMINAL = frozenset({MATCH_COMPLETED, MATCH_FORFEITED, MATCH_CANCELLED})
_STARTABLE = frozenset(
    {MATCH_SCHEDULED, MATCH_SERVER_ASSIGNED, MATCH_WARMUP, MATCH_LIVE}
)


class MatchStartError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _is_fake_server_id(server_id: str | None) -> bool:
    from app.application.commands.game_server_registry import is_fake_server_id

    return is_fake_server_id(server_id)


def _pick_live_server_id(uow: UnitOfWork, *, match_id: str) -> str | None:
    """Prefer srv_local / Bridge :27099 (may be stolen later with force=True)."""
    servers = uow.game_servers.list(limit=100)

    def is_local_bridge(server) -> bool:  # type: ignore[no-untyped-def]
        if server.id == "srv_local":
            return True
        url = server.endpoint_url or ""
        return "27099" in url

    for server in servers:
        if is_local_bridge(server) and server.endpoint_url:
            # Prefer free; else still return so force assign can steal
            if server.assigned_match_id in {None, match_id}:
                return server.id
    for server in servers:
        if is_local_bridge(server) and server.endpoint_url:
            return server.id
    return None


def start_match_fake(
    uow: UnitOfWork,
    *,
    match_id: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """
    Mark match live for Fake / admin path (GATE without CS2 VPS).

    Sets game_server_id=srv_fake if unset, scene=ingame, rebuilds overlay.
    Idempotent if already live.
    """
    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    if match.status in _TERMINAL:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="terminal",
        )
    if match.status not in _STARTABLE and match.status != MATCH_LIVE:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="bad_status",
        )

    already = match.status == MATCH_LIVE
    if not already:
        match.status = MATCH_LIVE
        match.phase = "live"
        if not match.game_server_id:
            match.game_server_id = "srv_fake"
        if not match.map_name:
            match.map_name = "de_mirage"
        uow.matches.save(match)

    write_audit(
        uow,
        match_id=match.id,
        action=ACTION_ORGANIZER_MATCH_START,
        actor_type=ACTOR_ORGANIZER,
        tournament_id=match.tournament_id,
        payload={"already_live": already, "mode": "fake"},
        correlation_id=correlation_id,
    )

    patch_production(
        uow,
        match_id=match.id,
        desired_scene=SCENE_INGAME,
        correlation_id=correlation_id,
    )
    # patch_production already rebuilds overlay when scene changes
    if already:
        rebuild_overlay_snapshot(uow, match, correlation_id=correlation_id, notify=True)

    uow.commit()
    refreshed = uow.matches.get(match_id)
    assert refreshed is not None
    return {
        "match": refreshed.to_public_dict(),
        "mode": "fake",
        "note": "Fake start: без live CS2; для локального DS — POST …/start-live после assign-server.",
        "already_live": already,
    }


def start_match_live(
    uow: UnitOfWork,
    *,
    match_id: str,
    server_id: str | None = None,
    correlation_id: str | None = None,
    send_load_match: bool = True,
    transport: GameCommandTransport | None = None,
) -> dict[str, Any]:
    """
    Mark match live for a registered Bridge/DS (no Fake emulator).

    Optional server_id: assign that game-server first (replaces unset/Fake).
    Requires real game_server_id + game_endpoint_url afterwards.
    """
    from app.application.commands.game_server_registry import (
        RegistryConflict,
        assign_server_to_match,
    )

    match = uow.matches.get(match_id)
    if match is None:
        raise KeyError(f"match not found: {match_id}")
    if match.status in _TERMINAL:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="terminal",
        )
    if match.status not in _STARTABLE:
        raise MatchStartError(
            f"cannot start from status={match.status}",
            code="bad_status",
        )

    # Auto-assign when match has no real server (common: bracket match + registry has srv_local)
    resolve_id = server_id
    if not resolve_id and _is_fake_server_id(match.game_server_id):
        resolve_id = _pick_live_server_id(uow, match_id=match_id)
        if not resolve_id:
            local = uow.game_servers.get("srv_local")
            if local is not None and local.assigned_match_id not in {None, match_id}:
                raise MatchStartError(
                    f"srv_local сейчас привязан к матчу {local.assigned_match_id}. "
                    f"Либо открой тот матч и жми live-старт, либо: "
                    f".\\scripts\\live-cs2-local.ps1 -MatchId {match_id} "
                    "(перепривяжет Bridge к этому матчу).",
                    code="server_busy",
                )

    if resolve_id and (
        _is_fake_server_id(match.game_server_id) or match.game_server_id != resolve_id
    ):
        try:
            assign_server_to_match(
                uow,
                match_id=match_id,
                server_id=resolve_id,
                commit=False,
                force=True,
            )
        except RegistryConflict as exc:
            raise MatchStartError(exc.message, code="assign_conflict") from exc
        except KeyError as exc:
            raise MatchStartError(
                f"game server not found: {resolve_id} — "
                "register with POST /api/v1/game-servers or run live-cs2-local.ps1",
                code="server_not_found",
            ) from exc
        match = uow.matches.get(match_id)
        assert match is not None

    if _is_fake_server_id(match.game_server_id):
        raise MatchStartError(
            "live start: у этого матча нет живого сервера "
            f"(game_server_id={match.game_server_id!r}). "
            "Сервер в реестре ≠ привязка к матчу. "
            f"Запусти: .\\scripts\\live-cs2-local.ps1 -MatchId {match_id} "
            "или POST …/assign-server с srv_local. "
            "Не путать с кнопкой «Старт (Fake)».",
            code="no_live_server",
        )
    if not match.game_endpoint_url:
        raise MatchStartError(
            "game_endpoint_url missing — assign a server with endpoint_url "
            "(Bridge http://127.0.0.1:27099)",
            code="no_endpoint",
        )
    if not match.webhook_secret:
        raise MatchStartError(
            "webhook_secret missing — set on game-server register / assign",
            code="no_secret",
        )

    already = match.status == MATCH_LIVE
    if not already:
        match.status = MATCH_LIVE
        match.phase = "live"
        if not match.map_name:
            match.map_name = "de_mirage"
        uow.matches.save(match)

    write_audit(
        uow,
        match_id=match.id,
        action=ACTION_ORGANIZER_MATCH_START,
        actor_type=ACTOR_ORGANIZER,
        tournament_id=match.tournament_id,
        payload={
            "already_live": already,
            "mode": "live",
            "game_server_id": match.game_server_id,
        },
        correlation_id=correlation_id,
    )

    patch_production(
        uow,
        match_id=match.id,
        desired_scene=SCENE_INGAME,
        correlation_id=correlation_id,
    )
    if already:
        rebuild_overlay_snapshot(uow, match, correlation_id=correlation_id, notify=True)

    load_ack: dict[str, Any] | None = None
    if send_load_match and not already:
        client = transport or HttpGameCommandTransport()
        ack = client.send(
            endpoint_base=match.game_endpoint_url,
            command_id=str(uuid4()),
            command_type=TYPE_LOAD,
            match_id=match.id,
            server_id=match.game_server_id,
            payload={"map": match.map_name or "de_mirage"},
            correlation_id=correlation_id,
        )
        load_ack = {
            "ack_status": ack.ack_status,
            "http_status": ack.http_status,
            "error": ack.error,
            "note": "Bridge may stub LoadMatch until MatchZy load is wired",
        }

    uow.commit()
    refreshed = uow.matches.get(match_id)
    assert refreshed is not None

    bridge_status = _probe_bridge_health(
        refreshed.game_endpoint_url,
        expect_match_id=refreshed.id,
        expect_server_id=refreshed.game_server_id,
    )
    if bridge_status.get("ok"):
        note = (
            f"Live OK: Bridge на связи (match_id={bridge_status.get('match_id')}, "
            f"seq={bridge_status.get('last_sequence')}). "
            "Счёт обновится на round_end."
        )
    elif bridge_status.get("reachable"):
        note = (
            "Live: Bridge отвечает, но MatchId/ServerId не совпадают с матчем — "
            "перепиши config.json и перезапусти dedicated. "
            f"Ожидалось {refreshed.id}/{refreshed.game_server_id}, "
            f"сейчас {bridge_status.get('match_id')}/{bridge_status.get('server_id')}."
        )
    else:
        note = (
            "Live: матч в статусе live, но Bridge сейчас не отвечает. "
            "Запусти/перезапусти dedicated (STK.Bridge :27099), "
            "сверь MatchId в config.json."
        )

    return {
        "match": refreshed.to_public_dict(),
        "mode": "live",
        "note": note,
        "already_live": already,
        "load_match": load_ack,
        "bridge_status": bridge_status,
        "bridge_config": {
            "MatchId": refreshed.id,
            "ServerId": refreshed.game_server_id,
            "CommandListenPort": _port_hint(refreshed.game_endpoint_url),
            "EventsPath": "/api/v1/internal/cs2/events",
            "WebhookSecret": "(same as CS2_WEBHOOK_SECRET / game-servers.webhook_secret — not returned)",
        },
        "judge_pause": (
            "Pause/Resume идут на match.game_endpoint_url (Bridge POST /v1/commands) "
            "после assign — тот же путь, что у Fake."
        ),
    }


def _probe_bridge_health(
    endpoint_url: str | None,
    *,
    expect_match_id: str,
    expect_server_id: str | None,
) -> dict[str, Any]:
    """Best-effort GET {endpoint}/health — does not fail start-live."""
    import json
    import urllib.error
    import urllib.request

    if not endpoint_url:
        return {"reachable": False, "ok": False, "error": "no endpoint"}
    url = endpoint_url.rstrip("/") + "/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {"reachable": False, "ok": False, "error": str(exc)}

    mid = body.get("match_id")
    sid = body.get("server_id")
    role = body.get("role")
    ids_ok = mid == expect_match_id and (
        expect_server_id is None or sid == expect_server_id
    )
    role_ok = role in (None, "stk-bridge")
    return {
        "reachable": True,
        "ok": bool(ids_ok and role_ok),
        "role": role,
        "match_id": mid,
        "server_id": sid,
        "last_sequence": body.get("last_sequence"),
        "bridge_version": body.get("bridge_version"),
    }


def _port_hint(endpoint_url: str | None) -> int | None:
    if not endpoint_url:
        return None
    try:
        # http://127.0.0.1:27099 → 27099
        hostport = endpoint_url.rstrip("/").split("//", 1)[-1]
        if ":" in hostport:
            return int(hostport.rsplit(":", 1)[-1].split("/")[0])
    except (ValueError, IndexError):
        return None
    return None
