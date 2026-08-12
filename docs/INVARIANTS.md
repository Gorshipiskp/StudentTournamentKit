# StudentTournamentKit — архитектурные инварианты и reconciliation

> Версия 1.0 · 2026-08-11  
> Источник: ревью системного дизайна · дополняет [ARCHITECTURE.md](ARCHITECTURE.md) · [DECISIONS.md](DECISIONS.md)

**Формула системы:**

> **Events** — низкая задержка распространения.  
> **State** — истина (platform-owned / runtime-owned).  
> **Snapshots** — восстановление.  
> **Reconciliation** — согласованность после сбоев.

Описание системы: **modular monolith with distributed execution boundaries and state reconciliation.**

---

## 1. Источники истины (не одна MySQL)

MySQL — **durable source of truth for platform-owned state**, не для всего мира.

| Данные | Авторитет |
|--------|-----------|
| Tournament, bracket, schedule | Platform DB |
| Match lifecycle (platform view) | Platform DB |
| Round state, actual game score | **CS2** |
| OBS scene (actual) | **OBS** |
| Director / Agent connection | Agent |
| WebRTC peer state | Browser / Agent |
| Overlay effective state | Platform-derived (merge) |
| Demo file bytes | CS2 disk → **durable store after match** |
| Audit | Platform DB |

**Запрещено:** писать `match.score = …` в DB как «истину» вместо обработки game event / snapshot.

---

## 2. Инварианты (нарушение = architectural bug)

| ID | Инвариант |
|----|-----------|
| **A1** | CS2 match execution never requires Platform availability (best-effort к Platform, кроме сознательных operator commands). |
| **A2** | Platform-owned state is persisted **before** external side effects are acknowledged as done. |
| **A3** | External state is never assumed from command acceptance; **actual** state is observed separately. |
| **A4** | All game events are **normalized** before entering match domain (no MatchZy/RCON types in domain). |
| **A5** | All external commands have **idempotent** semantics (`command_id` + ack). |
| **A6** | All realtime delivery is recoverable from an **authoritative snapshot**. |
| **A7** | Domain layer has **no** dependency on external protocols (RCON, OBS WS, ICE). |
| **A8** | Agent is the **only** OBS control authority (dashboard never talks to OBS). |
| **A9** | v1 Platform API runs as a **single replica** (in-memory WS hub). |
| **A10** | Every operator action is **auditable** (with correlation_id). |
| **A11** | CS2 → Platform: heartbeat, round events, overlay sync — **best-effort**. Pause / unpause / forfeit / load_match — **command path** with delivery semantics. |
| **A12** | Production **desired** state is authoritative; scene **commands** are transient. On Agent reconnect → apply desired, do not replay command history. |

---

## 3. Три измерения состояния (не смешивать)

### 3.1 MatchStatus (lifecycle)

```text
scheduled → server_assigned → warmup → knife → live → map_end
                                                      ↓
                                              (next map | completed)
side: cancelled | forfeited
```

`tech_pause` **не** является MatchStatus. Матч остаётся `live`, пока идёт тех. пауза.

### 3.2 ReviewStatus (judge workflow)

```text
none → requested → pause_pending → paused → resolved
         │                           │
         └── cancelled ◄─────────────┘
```

Resolved outcomes: `continue` | `forfeit` (forfeit меняет MatchStatus).

### 3.3 Production (раздельно, не одна FSM)

| Поле | Значения (пример) |
|------|-------------------|
| `agent_status` | disconnected · connected · degraded |
| `obs_status` | disconnected · connected |
| `broadcast_status` | unknown · idle · streaming |
| `desired.scene` | waiting · intro · teams · ingame · … |
| `actual.scene` | то же (из OBS через Agent) |
| `desired.stream` | off · on |
| `actual.stream` | off · on · unknown |

Валидно: `agent=connected`, `obs=disconnected`, `broadcast=unknown`.

### 3.4 TournamentStatus (уточнение)

```text
draft → published → live → completed → archived
                 ↘ cancelled
```

- `published` — конфигурация/сетка достаточно зафиксированы, приглашения активны; матч ещё не обязан идти.  
- `completed` — соревнование закончено.  
- `archived` — ephemeral operational data можно чистить; read-only история остаётся.

---

## 4. Desired vs actual

```text
┌───────────────────────┐
│   Platform DB state   │
│  authoritative intent │
└───────────┬───────────┘
            │ desired
      reconciliation
     ┌──────┴──────┐
     ↓             ↓
CS2 actual     OBS actual (via Agent)
     │             │
     └──────┬──────┘
            ↓
    events (fast path)
    snapshots (recovery)
```

| Пара | Desired (Platform) | Actual (runtime) |
|------|--------------------|------------------|
| Game pause | `desired.paused` | CS2 snapshot / event |
| Scene | `desired.scene` | Agent report from OBS |
| Stream delay | `configured_broadcast_delay_seconds` | OBS (не verified в v1) |

**Command ≠ success:** `POST /production/scene` ставит **desired**. Agent подтверждает **actual**. UI: «Pause pending», если desired≠actual.

---

## 5. Events: два класса + outbox

### 5.1 Domain events (внутри транзакции)

Описывают «что произошло в домене»: `MatchReviewRequested`, `MatchCompleted`, `MatchForfeited`, …

Пишутся в тот же UoW, что и aggregate update.

### 5.2 Integration / side-effect events (после commit)

`notify_overlay`, `notify_agent`, `broadcast_ws`, `write_audit`, `revoke_tokens`, …

### 5.3 MySQL outbox (без Kafka/Redis/Celery)

```text
DB transaction
├── update aggregate
├── append domain event → event_outbox
└── commit
       ↓
in-process dispatcher (after commit)
       ↓
handlers (WS / Agent / audit)
```

Таблица `event_outbox`: `id`, `event_type`, `aggregate_type`, `aggregate_id`, `payload`, `correlation_id`, `created_at`, `processed_at`.

На startup: scan `processed_at IS NULL` → replay.

WS delivery остаётся ephemeral; **business transition** не теряется с Python process.

---

## 6. Game events: idempotency + sequence + snapshot

### Webhook payload (обязательные поля)

```json
{
  "event_id": "uuid",
  "sequence": 183,
  "server_id": "srv_abc",
  "match_id": "m_xyz",
  "type": "round_end",
  "timestamp": "2026-08-11T16:00:00Z",
  "correlation_id": "…",
  "payload": { }
}
```

| Механизм | Роль |
|----------|------|
| `event_id` UNIQUE в той же транзакции, что update | Transport dedup |
| `sequence` per match (or per server) | Detect gaps / out-of-order |
| Idempotent handler | Domain safety: `apply(e); apply(e)` safe |
| **Game snapshot** | Recovery / reconciliation |

### Game snapshot (обязателен)

```json
{
  "match_id": "…",
  "map": "de_mirage",
  "round": 12,
  "score": [7, 5],
  "phase": "freeze",
  "paused": false,
  "loaded": true,
  "players": []
}
```

```text
event stream  → normal operation (fast path)
snapshot      → recovery / reconciliation
```

### Commands Platform → CS2

```text
intent → command (command_id) → game → ack → actual state
```

Не: `HTTP 200 = command succeeded`.

Команды: `PauseMatch`, `ResumeMatch`, `ForfeitMatch`, `LoadMatch`, `GetSnapshot` — **whitelist**. Никакого raw RCON из application layer.

Состояния команды: `requested → sent → confirmed | failed` (минимум desired/actual pause flags).

---

## 7. Production: reconciler, не только CommandQueue

Agent — **state reconciler**:

```text
Platform desired.scene = ingame
Agent reads OBS actual.scene = intro
Agent: SetCurrentProgramScene(ingame)
actual = ingame
```

| Тип | Примеры |
|-----|---------|
| **State (reconcile)** | scene, stream on/off |
| **Commands (imperative)** | refresh_browser_source, restart_obs_hint |

На reconnect Agent получает **desired production state**, не историю команд.

**Whitelist OBS protocol:** `obs.set_scene`, `obs.start_stream`, `obs.stop_stream`, `obs.refresh_browser_source`, … — не произвольный `obs.execute`.

---

## 8. Overlay: snapshot, не patch (v1)

WS:

```json
{
  "protocol": 1,
  "type": "overlay.snapshot",
  "version": 42,
  "data": { "scene": "ingame", "team_a": {}, "team_b": {}, "round": 12 }
}
```

- Payload маленький → full snapshot проще и безопаснее patch.  
- `version` — **per match** (`overlay_revision`), monotonic, DB/transactional (не in-memory counter).  
- На reconnect: GET/WS snapshot, client state не важен.

---

## 9. Reconciliation loops

Не постоянно на максимуме — по heartbeat / reconnect / startup.

### Platform restart

```text
load active matches → reconcile CS2 snapshots → rebuild overlay → agents reconnect to desired
```

### Agent restart

```text
auth → get desired production → query OBS actual → reconcile → report
```

### Bridge restart

```text
heartbeat → get snapshot → compare → resume event stream (sequence)
```

### Missed / out-of-order events

```text
sequence gap → request snapshot → repair platform view
```

---

## 10. Concurrency

- Aggregates: `matches.version` (optimistic locking) для критических transitions.  
- При необходимости: `SELECT … FOR UPDATE` на match row.  
- Judge UI: server FSM authoritative — stale resolve rejected.  
- Concurrent: judge forfeit vs continue vs round_end webhook — version/lock.

---

## 11. Correlation ID

`correlation_id` / `X-Request-ID` проходит:

```text
Dashboard → API → outbox → CS2 command → Bridge → webhook → API → overlay / WS
```

Audit: `request_id`, `correlation_id`, `actor_*`, `match_id`, `tournament_id`, `action`, `payload`, `result`, `created_at`.

---

## 12. Protocol / version compatibility

| Компонент | Поле |
|-----------|------|
| Platform | `api_version`, `protocol_version` |
| Agent | `agent_version`, `protocol_version` → dashboard: compatible? |
| STK.Bridge | `bridge_version`, `protocol_version` в heartbeat |

WS messages: `"protocol": 1`.

---

## 13. Demo lifecycle (до teardown CS2)

```text
match ends → demo finalized on CS2 disk
          → copy/upload to durable storage (Platform volume / object / organizer MySQL path — TBD v1)
          → demo_files points to durable location
          → CS2 VPS may be destroyed
```

**Запрещено:** считать demo «сохранённым», пока файл только на ephemeral CS2 VPS.

---

## 14. Health ≠ heartbeat

Компонентный health:

```text
Reachability · Event freshness · Command path · State consistency
```

Aggregate: `HEALTHY | DEGRADED | OFFLINE | UNKNOWN`.

Пример CS2:

```text
reachable ✓  heartbeat ✓  events ✓  command_ack ✓  state_sync ✓
```

`/health` — process alive (без DB).  
`/ready` — can serve (DB). TURN down ≠ API not ready.

---

## 15. Operational constraints (v1)

| Constraint | Правило |
|------------|---------|
| API replicas | **Exactly 1** (ADR) |
| Redis | Только когда replicas > 1 (WS fanout) |
| `configured_broadcast_delay_seconds` | Desired config; OBS actual not verified in v1 |
| Branding BLOB | Soft limits (logo ≤ 2 MB, bg ≤ 5 MB); migration path later |
| MySQL | Backup + restore test в Production Ready |
| Frontend layers | Backend strict 4-layer; frontend — **feature-oriented**, не церемония на каждый CRUD |

---

## 16. Acceptance: первый vertical slice должен включать отказы

Помимо happy path:

| Test | Сценарий |
|------|----------|
| A | Platform restart during match |
| B | Agent restart during live |
| C | Duplicate webhook |
| D | Out-of-order webhook |
| E | Judge resolve race with round event |

Если A–E проходят — архитектура существует в runtime, не только на диаграмме.  
Человеческий runbook: [PRODUCTION-RECOVERY.md](PRODUCTION-RECOVERY.md).

---

## Связанные документы

- [ARCHITECTURE.md](ARCHITECTURE.md) — обновлённые state machines, CS2, recovery  
- [DECISIONS.md](DECISIONS.md) — ADR-025+  
- [LAYERS.md](LAYERS.md) — D8 как capability; state dimensions  
- [TECH-STACK.md](TECH-STACK.md) — outbox, overlay snapshot  

---

*Нарушение A1–A12 в PR = architectural bug, не «стилистическое замечание».*
