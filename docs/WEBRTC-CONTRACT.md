# WebRTC contract (People Slice)

> Short protocol for Agent publisher ↔ commentator subscribers.  
> Frozen: **F1** video from director laptop · **F2** P2P + TURN, no SFU · **F7** audio off in v1.

## Roles

| Role | Who | Auth |
|------|-----|------|
| **publisher** | Director Agent | `STK_AGENT_TOKEN` (same as `/ws/agent`) |
| **subscriber** | Commentator browser (1–2) | Invite session with `commentator.watch` |

Platform **only relays signaling** and issues TURN credentials. Media is P2P (via TURN if needed).

## Endpoints

| Channel | URL |
|---------|-----|
| Signaling WS | `/ws/signaling/{matchId}?role=publisher\|subscriber&token=…` |
| TURN credentials | `POST /api/v1/matches/{matchId}/turn-credentials` (Bearer invite **or** agent token) |

`token` query: agent secret **or** invite **access_token** (after redeem).

## Protocol

- **version:** `protocol: 1` on every JSON message  
- **Offer direction:** **publisher creates offer** after `signaling.peer_joined` (subscriber); subscriber answers  
- **Max subscribers:** **2** per match (extra connects get close `4429`)  
- **Audio:** not negotiated in v1 (video-only)
- **UI:** commentator opens `/watch?token=<invite>` (or `/watch/<invite>`); status from overlay snapshot WS; video via this signaling channel. `?mock=1` shows a local canvas stream without Agent (dev / P4 DoD).
- **Agent:** `--fake-webrtc` publishes looping VP8 test pattern (Pion). Signaling reconnect is independent of OBS Agent WS / reconcile (A12).

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

## TURN

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

## Non-goals (this contract)

- SFU / LiveKit  
- Commentator → Agent media  
- Audio tracks  
- Recording
