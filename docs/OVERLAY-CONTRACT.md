# Overlay + Production contract (v1)

> Source of truth for Platform ↔ Overlay SPA ↔ Director Agent.  
> Invariants: [INVARIANTS.md](INVARIANTS.md) §3.3 · §7 · §8 · A8 · A12.  
> TZ: [tasks/003_PRODUCTION-SLICE.md](../tasks/003_PRODUCTION-SLICE.md).

**protocol:** `1`  
**Transport:** HTTP GET snapshot · WebSocket full snapshot (no patch in v1).

---

## 1. Overlay snapshot message

Every WS frame and `GET /api/v1/matches/{matchId}/overlay` body:

```json
{
  "protocol": 1,
  "type": "overlay.snapshot",
  "match_id": "m_…",
  "version": 42,
  "data": {
    "scene": "ingame",
    "team_a": { "name": "Team A", "score": 7 },
    "team_b": { "name": "Team B", "score": 5 },
    "map": "de_mirage",
    "round": 12,
    "phase": "live",
    "match_status": "live",
    "paused": false,
    "judge": { "status": "none", "banner": null },
    "watermark": { "text": "STP", "visible": true },
    "branding": {
      "logo_url": "/api/v1/tournaments/{id}/branding/logo",
      "bg_url": null,
      "colors": { "primary": "#3d9a86", "accent": "#c9a227" }
    }
  }
}
```

| Field | Rules |
|-------|--------|
| `version` | Per-match `overlay_revision`, monotonic, DB-backed. Bumps on merge (score/status/scene/override). |
| `type` | Always `overlay.snapshot` (full state). |
| `branding` | Optional (TZ005). `logo_url` / `bg_url` are same-origin API paths; watermark always remains. |
| `data.scene` | Layout key from production **desired** scene (director). |
| `data.team_*`.score | From match game view (Fake/CS2), unless temporary manual override. |
| `data.watermark.visible` | Always `true` — no client flag to hide (F4). |
| `data.judge.banner` | e.g. `tech_pause` / `review_requested` / `null`. |

### Endpoints

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `/api/v1/matches/{matchId}/overlay` | Current snapshot (`version` + `data`). |
| `WS` | `/ws/overlay/{matchId}` | On connect → full snapshot; on update → full snapshot again. |
| `POST` | `/api/v1/matches/{matchId}/overlay/override` | Manual override (P5+; stub allowed later). |

Reconnect: client discards local state; applies latest snapshot. Patch protocol is out of v1.

### Merge priority (conflict)

```text
judge_banner > manual_overrides (TTL) > game_state (score/round/map)
production.desired.scene → data.scene
```

---

## 2. Production desired / actual

Platform-owned row per match (`production_sessions`). Agent reconciles OBS to **desired**; reports **actual**. Dashboard never talks to OBS (A8).

| Field | Example values |
|-------|----------------|
| `desired.scene` | `waiting` · `intro` · `teams` · `ingame` · `break` · `winner` |
| `actual.scene` | same set, or `null` until Agent reports |
| `desired.stream` | `off` · `on` |
| `actual.stream` | `off` · `on` · `unknown` |
| `agent_status` | `disconnected` · `connected` · `degraded` |
| `obs_status` | `disconnected` · `connected` |
| `broadcast_status` | `unknown` · `idle` · `streaming` |

### HTTP (P3+)

| Method | Path | Behavior |
|--------|------|----------|
| `GET` | `/api/v1/matches/{id}/production` | desired + actual + agent/obs/broadcast |
| `PATCH` | `/api/v1/matches/{id}/production` | update `desired.scene` / stream flags |

### Agent session WS (P3+)

| Method | Path | Auth |
|--------|------|------|
| `WS` | `/ws/agent/{matchId}?token=` | `STK_AGENT_TOKEN` (or header `X-STK-Agent-Token`) |

On connect → push current `production.desired`. On PATCH desired → outbox → hub push.  
On reconnect: apply **desired**, do not replay command history (A12).

---

## 3. Agent ↔ Platform WS (minimum message types)

Channel (P3–P4): Agent session WS (auth stub token/env). Not the overlay Browser Source socket.

| `type` | Direction | Purpose |
|--------|-----------|---------|
| `agent.hello` | Agent → Platform | session start; protocol/version |
| `production.desired` | Platform → Agent | full desired push (scene, stream) |
| `production.actual` | Agent → Platform | observed OBS scene/stream/status |
| `agent.ping` / `agent.pong` | both | liveness (optional) |

Imperative one-shots (later): `obs.refresh_browser_source` — not SoT; desired remains authoritative.

---

## 4. Outbox side effects

| `event_type` | After | Handler |
|--------------|-------|---------|
| `overlay.updated` | overlay revision persisted | in-memory WS hub broadcast (`notify_overlay`) |
| `production.desired_changed` | PATCH desired (P3) | notify Agent channel |

Business transition is durable in MySQL **before** WS fanout (A2, F5).
