# WebRTC / media contract (People Slice)

> Dual-mode: **protocol 1** = Fake/CI P2P · **protocol 2** = live OBS WHIP → MediaMTX → WHEP.  
> Frozen: **F1** video from director laptop · **F4** audio off · **F5** CI = Fake without MediaMTX · **F7** secrets not in git · **F9** path `stk/<matchId>`, ≤2 WHEP.  
> ADR: **[ADR-037](DECISIONS.md#adr-037--комментаторы-live-obs-whip--mediamtx--whep)** (live) · ADR-022 (Fake only).

## Modes

| Mode | Protocol | When | Media path | Platform role |
|------|----------|------|------------|---------------|
| **Fake / CI** | **1** | verify, репетиции без OBS | Agent `--fake-webrtc` → P2P (+ TURN) | Signaling WS + TURN credentials |
| **Live** | **2** | матч / owner smoke | OBS **WHIP** → **MediaMTX** → `/watch` **WHEP** | Mint WHIP/WHEP URL+bearer; **не** Pion signaling for video |
| **Legacy live** | 1 | deprecated (TZ008) | Virtual Cam → FFmpeg → Pion | Same as Fake signaling; do not use as canon |

`media.mode` (API / bootstrapping, P3–P4): `fake` | `whep` | `mock` (`?mock=1` local canvas).

---

## Protocol 1 — Fake P2P (unchanged semantics)

### Roles

| Role | Who | Auth |
|------|-----|------|
| **publisher** | Director Agent | `STK_AGENT_TOKEN` (same as `/ws/agent`) |
| **subscriber** | Commentator browser (1–2) | Invite session with `commentator.watch` |

Platform **only relays signaling** and issues TURN credentials. Media is P2P (via TURN if needed). **No MediaMTX required.**

### Endpoints

| Channel | URL |
|---------|-----|
| Signaling WS | `/ws/signaling/{matchId}?role=publisher\|subscriber&token=…` |
| TURN credentials | `POST /api/v1/matches/{matchId}/turn-credentials` (Bearer invite **or** agent token) |

`token` query: agent secret **or** invite **access_token** (after redeem).

### Protocol rules

- **version:** `protocol: 1` on every JSON message  
- **Offer direction:** **publisher creates offer** after `signaling.peer_joined` (subscriber); subscriber answers  
- **Max subscribers:** **2** per match (extra connects get close `4429`)  
- **Audio:** not negotiated (video-only)
- **UI:** `/watch?token=<invite>` (or `/watch/<invite>`); `?mock=1` = local canvas without Agent
- **Agent:** `--fake-webrtc` = looping VP8 test pattern (Pion). Signaling reconnect independent of OBS Agent WS (A12).

### Message types

| `type` | Direction | Fields |
|--------|-----------|--------|
| `signaling.hello` | Platform → peer | `role`, `peer_id`, `match_id`, `protocol` |
| `signaling.peer_joined` | Platform → publisher | `peer_id`, `role` |
| `signaling.peer_left` | Platform → others | `peer_id` |
| `signaling.offer` | publisher → subscriber | `from`, `to`, `sdp` |
| `signaling.answer` | subscriber → publisher | `from`, `to`, `sdp` |
| `signaling.ice` | either → peer | `from`, `to`, `candidate` (RTCIceCandidateInit JSON) |
| `error` | Platform → peer | `detail` |

Relay rules: Platform forwards `offer` / `answer` / `ice` only if `from` matches sender `peer_id` and `to` is connected on the same match. Unknown `to` → `error`.

### Example flow

```text
subscriber connect → hello(subscriber)
publisher gets peer_joined(subscriber_id)
publisher → offer(to=subscriber_id)
subscriber → answer(to=publisher_id)
both ↔ ice
```

### TURN (protocol 1)

- coturn on Platform (`docker compose --profile webrtc`)
- Time-limited credentials (HMAC / coturn `use-auth-secret`), default TTL **300s**
- Response shape:

```json
{
  "urls": ["turn:HOST:3478?transport=udp", "turn:HOST:3478?transport=tcp"],
  "username": "<expiry>:<matchId>",
  "credential": "<hmac>",
  "ttl": 300,
  "expires_at": "…"
}
```

Env: `TURN_HOST`, `TURN_PORT`, `TURN_SECRET`, `TURN_TTL_SECONDS`, `TURN_REALM` (see `.env.example`).

---

## Protocol 2 — Live WHIP / WHEP (MediaMTX)

### Roles

| Role | Who | Auth |
|------|-----|------|
| **publisher** | OBS on director laptop (WHIP) | Bearer from Platform `whip-publish` (organizer / director access) |
| **viewer** | Commentator `/watch` (WHEP) | Bearer from Platform `whep-play` (`commentator.watch` invite) |

Director Agent: **scenes only** (OBS WebSocket). Does **not** encode or publish live video in canon.

### Path (Frozen F9)

```text
stk/<matchId>
```

Derived URLs (base = `MEDIAMTX_PUBLIC_URL`, no trailing slash):

| Kind | URL |
|------|-----|
| WHIP | `{MEDIAMTX_PUBLIC_URL}/stk/{matchId}/whip` |
| WHEP | `{MEDIAMTX_PUBLIC_URL}/stk/{matchId}/whep` |

### Endpoints (Platform API — implement P3)

| Who | Method | Auth |
|-----|--------|------|
| Organizer / director panel | `POST /api/v1/matches/{matchId}/whip-publish` | organizer (or director role per existing auth) |
| Commentator | `POST /api/v1/matches/{matchId}/whep-play` | invite with `commentator.watch` |

### Credentials response shape (P3)

Same spirit as TURN: short TTL, no long-lived secrets in OBS/git.

**whip-publish:**

```json
{
  "path": "stk/<matchId>",
  "whip_url": "https://media.example/stk/<matchId>/whip",
  "bearer": "<token>",
  "ttl": 600,
  "expires_at": "…"
}
```

**whep-play:**

```json
{
  "path": "stk/<matchId>",
  "whep_url": "https://media.example/stk/<matchId>/whep",
  "bearer": "<token>",
  "ttl": 600,
  "expires_at": "…"
}
```

Rules:

- Bearer compatible with MediaMTX auth via Platform `POST /api/v1/internal/mediamtx-auth` (`authMethod: http` in mediamtx.yml). Token format HMAC `mtx.<payload>.<sig>` (`MEDIAMTX_AUTH_SECRET`).
- Default TTL short (**5–15 min**, env `MEDIAMTX_CREDENTIAL_TTL_SECONDS`); refresh from panel.
- **≤2** concurrent WHEP **holders** (invite) per match (in-memory on API; 3rd distinct invite → **429**). Same invite refresh/reconnect **replaces** its lease.
- No publisher on path → `/watch` shows clear status (not eternal Pion waiting_offer) — P4.
- Never log bearer values (F7).

### Media pipeline (live)

```text
OBS Program ──WHIP──► MediaMTX (Platform) ──WHEP──► /watch
Agent ──obs-websocket──► OBS (scenes only)
Platform API ──bearer URLs──► OBS + /watch
```

- Twitch RTMP may use OBS Stream Delay; **WHIP has no delay** (ADR-009 / ADR-024 / F6).
- Compose: `docker compose --profile whip` · config `infra/mediamtx/` · env `MEDIAMTX_PUBLIC_URL`, `MEDIAMTX_API_URL`, `MEDIAMTX_WEBRTC_ADDITIONAL_HOSTS`.
- ICE/NAT: `webrtcAdditionalHosts` + optional coturn in MediaMTX (`webrtcICEServers2`).

### Legacy live (TZ008 — not canon)

Virtual Cam → FFmpeg → VP8 → Pion + protocol 1 signaling. Flags `--live-webrtc` / device docs remain until P5 deprecate note. Prefer protocol 2 for match day.

---

## Non-goals (this contract)

- LiveKit Cloud / paid SFU-SaaS  
- Removing Fake/Pion in this wave  
- Commentator → director media (upstream)  
- Audio tracks in WebRTC (Voicemeeter / Discord outside platform)  
- Recording / DVR on MediaMTX  
- Twitch ingest via WHIP  
- FFmpeg Stream Delay for Twitch (stays OBS Stream Delay)

---

## References

- ADR-037 · ADR-022 (Fake) · ADR-008 (source = director laptop)  
- Spike: `workers/developer/notes/TZ011-SPIKE.md`  
- ТЗ: `tasks/011_OBS-WHIP.md` · legacy live: `tasks/008_LIVE-WEBRTC.md`
