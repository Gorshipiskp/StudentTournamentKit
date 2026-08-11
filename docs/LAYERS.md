# Student Tournament Platform — домены и слои

> Версия **1.1** · 2026-08-11  
> Дополняет [ARCHITECTURE.md](ARCHITECTURE.md) · [TECH-STACK.md](TECH-STACK.md) · [INVARIANTS.md](INVARIANTS.md)

---

## Содержание

1. [Зачем слои](#1-зачем-слои)
2. [Домены и capabilities](#2-домены-и-capabilities)
3. [Глобальная слоистая модель](#3-глобальная-слоистая-модель)
4. [Слои backend (apps/api)](#4-слои-backend-appsapi)
5. [Слои frontend](#5-слои-frontend)
6. [Слои Director Agent](#6-слои-director-agent)
7. [Game plane (CS2 VPS)](#7-game-plane-cs2-vps)
8. [Матрица домен → слой → артефакт](#8-матрица-домен--слой--артефакт)
9. [Зависимости и правила импорта](#9-зависимости-и-правила-импорта)
10. [Сквозные concerns](#10-сквозные-concerns)
11. [События между доменами](#11-события-между-доменами)

---

## 1. Зачем слои

STP — **модульный монолит**: один deployable API + distributed execution (CS2, Agent). Слои отделяют:

| Что | От чего |
|-----|---------|
| Бизнес-правила | HTTP, WebSocket, SQL, RCON |
| Use cases | UI-кнопок и DTO |
| Домен матча | Деталей MatchZy webhook JSON |
| Overlay layout | OBS WebSocket протокола |

**Правило зависимостей:** внешние слои зависят от внутренних. **Domain не знает** про FastAPI, Svelte, OBS, MySQL, RCON, ICE.

---

## 2. Домены и capabilities

### Business domains (bounded contexts)

```text
D1 Identity → D2 Tournament → D3 Competition → D4 Match
                                                ├─ D5 Game Integration
                                                ├─ D6 Production
                                                └─ D7 Overlay
```

### Platform capabilities (не BC)

```text
Realtime (WS, signaling transport)
Operations (health, audit)
Security / Persistence
```

Ранее D8/D9 как «домены» — переименованы в capabilities (ADR-036). Нумерация D1–D7 сохраняется для кода.

### D1 — Identity & Access

| Сущности | `User`, `InviteToken`, `Session`, `Permission` (capabilities) |
| Инварианты | Scoped tokens; revoke; secrets не в JWT |
| Роли / caps | `match.read`, `match.control`, `judge.review`, `judge.resolve`, `production.control`, `overlay.read` + scope |

### D2 — Tournament

| Сущности | `Tournament`, `TournamentBranding`, `TournamentSettings` |
| Инварианты | `draft→published→live→completed→archived`; `configured_broadcast_delay_seconds`; watermark always on |
| Не делает | Сетку, матчи |

### D3 — Competition

| Сущности | `Team`, `Player`, `BracketNode` (sources: team / winner_of / bye) |
| Инварианты | 5+coach; single elim; manual structure для non-2^n |
| Не делает | Live match state |

`BracketNode.match_id` — immutable reference на Match (событие ≠ позиция в графе).

### D4 — Match (ядро)

| Сущности | `Match` (`status` + `review_status` + `version`), `MatchMap`, `DemoFile`, stats |
| Инварианты | Отдельные измерения Match/Review; optimistic `version`; score только из game events/snapshot |
| Владеет | Platform view матча; desired game commands |

### D5 — Game Integration

| Сущности (domain) | `GameServer`, `GameEvent` (normalized), `GameCommand` |
| Инфраструктура (не domain) | RCON client, webhook parser, HMAC |
| Инварианты | Normalize before domain; idempotent commands; sequence; snapshot reconcile |
| Anti-corruption | MatchZy/CSS → RoundStarted / ScoreChanged / … |

### D6 — Production

| Сущности | `ProductionSession` (desired/actual scene, agent/obs/broadcast status) |
| Инварианты | Agent sole OBS authority; whitelist commands; reconcile on reconnect |
| Не делает | Overlay HTML, game score |

### D7 — Overlay

| Сущности | `OverlaySnapshot`, merge inputs, overrides (TTL / until game event) |
| Инварианты | Pure `merge()`; per-match revision; watermark always |
| WS | `overlay.snapshot` full state |

### Realtime / Operations (capabilities)

Transport + health/audit. Не содержат tournament business rules.

---

## 3. Глобальная слоистая модель

Платформа целиком — **4 слоя + edge**, повторяющиеся в каждом deployable.

```text
┌─────────────────────────────────────────────────────────────┐
│ L0  EDGE          nginx · TLS · rate limit · static files   │
├─────────────────────────────────────────────────────────────┤
│ L1  PRESENTATION  HTTP routers · WS handlers · UI pages   │
│                   DTO in/out · не бизнес-логика             │
├─────────────────────────────────────────────────────────────┤
│ L2  APPLICATION   Use cases · orchestration · transactions  │
│                   Commands / Queries · domain event dispatch│
├─────────────────────────────────────────────────────────────┤
│ L3  DOMAIN        Entities · value objects · state machines │
│                   Domain services · domain events · rules   │
├─────────────────────────────────────────────────────────────┤
│ L4  INFRASTRUCTURE Repositories · CS2 adapter · WS hub      │
│                   OBS agent client · MySQL · FFmpeg capture / coturn  │
└─────────────────────────────────────────────────────────────┘
```

### Что в каком слое (на примере «судья запросил проверку»)

| Слой | Код | Делает |
|------|-----|--------|
| L1 | `POST /matches/{id}/judge/review-request` | Валидация JSON, auth token |
| L2 | `JudgeService.request_review(match_id)` | Открывает транзакцию, вызывает domain |
| L3 | `Match.request_review()` | Проверяет state==live, ставит review_requested |
| L3 | event `MatchReviewRequested` | — |
| L2 | handler | Audit log, notify D7 banner, push D8 WS |
| L4 | `MatchRepository.save()`, `WSHub.broadcast()` | Персистенция, доставка |

---

## 4. Слои backend (`apps/api`)

### 4.1 Структура каталогов

```text
apps/api/
  app/
    presentation/                 # L1
      http/
        routers/
          auth.py
          tournaments.py
          matches.py
          judge.py
          production.py
          internal_cs2.py
        middleware/
        schemas/                  # Pydantic request/response ONLY
      ws/
        router.py
        channels/
        schemas/

    application/                # L2
      services/
        auth_service.py
        tournament_service.py
        competition_service.py
        match_service.py
        judge_service.py
        production_service.py
        overlay_service.py
        game_integration_service.py
        signaling_service.py
        operations_service.py
      commands/                   # write use cases (optional explicit)
      queries/                    # read use cases
      handlers/                   # domain event → side effects
      unit_of_work.py

    domain/                       # L3
      identity/
        entities.py
        events.py
        ports.py                  # abstract repos (interfaces)
      tournament/
      competition/
      match/
        state_machine.py
        entities.py
        events.py
      production/
      overlay/
        merge_policy.py           # merge(game, manual, judge)
      game_integration/
        events.py                 # normalized game events
        ports.py                  # GameServerPort
      shared/
        value_objects.py          # Score, MapName, SteamId
        exceptions.py

    infrastructure/               # L4
      persistence/
        sqlalchemy/
          models.py               # ORM tables
          repositories/           # implements domain ports
      adapters/
        cs2/
          webhook_parser.py
          rcon_client.py
          event_normalizer.py
      realtime/
        ws_hub.py
        signaling_relay.py
      security/
        jwt.py
        token_hasher.py
        hmac_webhook.py
      config.py

    main.py                       # composition root (DI wiring)
```

### 4.2 Маппинг доменов на application services

| Домен | Application Service | Domain module | Infrastructure |
|-------|---------------------|---------------|----------------|
| D1 | `AuthService` | `domain/identity/` | `security/`, repos |
| D2 | `TournamentService` | `domain/tournament/` | repos, BLOB storage |
| D3 | `CompetitionService` | `domain/competition/` | repos |
| D4 | `MatchService` | `domain/match/` | repos, state machine |
| D5 | `GameIntegrationService` | `domain/game_integration/` | `adapters/cs2/` |
| D6 | `ProductionService` | `domain/production/` | WS → agent queue |
| D7 | `OverlayService` | `domain/overlay/` | WS hub broadcast |
| D8 | `SignalingService` | — (thin) | `realtime/` |
| D9 | `OperationsService` | — | audit repo, health |

### 4.3 Domain layer — ключевые state machines

Только в `domain/`, без FastAPI/SQLAlchemy:

```text
domain/match/state_machine.py      MatchStatus transitions
domain/match/judge_flow.py         review_requested → tech_pause
domain/production/scene_fsm.py     scene command lifecycle
domain/overlay/merge_policy.py     приоритеты snapshot
```

### 4.4 Ports & Adapters (D5 пример)

```python
# domain/game_integration/ports.py  (interface)
class GameServerPort(Protocol):
    async def pause_match(self, server_id: str, match_id: str) -> None: ...
    async def forfeit(self, server_id: str, winner_team_id: str) -> None: ...

# infrastructure/adapters/cs2/rcon_adapter.py  (implementation)
class CS2RconAdapter(GameServerPort): ...
```

D4 `MatchService` зависит от `GameServerPort`, не от RCON напрямую.

---

## 5. Слои frontend

Backend — строгие 4 слоя. Frontend — **feature-oriented**, без церемонии 4 каталогов на каждый CRUD (ADR-036).

### 5.1 Структура (рекомендация)

```text
apps/dashboard/src/
  features/
    matches/
    production/
    bracket/
    tournaments/
  shared/
    api/          # OpenAPI-generated client
    ws/
    ui/
```

Принцип: domain/pure logic не зависит от `fetch`, но не обязательно `presentation/application/domain/infrastructure` в каждом feature.

### 5.2 Маппинг UI → домены

| UI App | Домены | Routes |
|--------|--------|--------|
| `dashboard` | D2, D3, D4, D6 + Ops | `/admin/*`, `/director/[matchId]` |
| `overlay` | D7 + Realtime | `/overlay/[matchId]`, `/watch/[token]` |
| `judge` | D4 review + Realtime | `/judge/[token]` |

### 5.3 Shared package

```text
packages/api-types/   # generated from FastAPI OpenAPI (API contract only)
```

---

## 6. Слои Director Agent

Отдельный deployable, но та же 4-слойная логика.

```text
apps/director-agent/
  cmd/agent/              # entrypoint
  internal/
    presentation/         # L1 — WS to platform, local HTTP setup UI
      platform_ws/
      setup_http/
    application/          # L2 — use cases
      session_manager.go
      scene_executor.go
      stream_publisher.go
    domain/               # L3
      command.go          # OBSCommand, SceneMapping
      session.go
      events.go
    infrastructure/       # L4
      obs/client.go
      webrtc/publisher.go
      capture/ffmpeg.go
      # delay/ffmpeg_twitch.go   # v2 only — Twitch delay fallback
```

### Маппинг доменов на Agent

| Platform домен | Agent слой | Действие |
|----------------|------------|----------|
| D6 Production | application `SceneExecutor` | Выполняет OBS commands |
| D8 Real-time | presentation `platform_ws` | Signaling relay |
| D8 Real-time | infrastructure `webrtc` | Publishes video |
| D6 | OBS Stream Delay (вне Agent, v1) | Delayed Twitch; FFmpeg delay — v2 |

Agent **не содержит** tournament/bracket logic — только match-scoped session.

---

## 7. Game plane (CS2 VPS)

Не часть `apps/api`, но домен D5 имеет **внешнюю реализацию** на сервере.

```text
┌────────── Game Plane ──────────┐
│  L1  STP.Bridge HTTP callbacks │  → Platform webhooks
│  L2  Bridge orchestration      │  judge pause hook, heartbeat
│  L3  MatchZy domain            │  match flow (reuse)
│  L4  CS2 engine + CSS runtime  │
└────────────────────────────────┘
```

| Слой | Компонент | Не знает про |
|------|-----------|--------------|
| L1 | STP.Bridge HTTP client | MySQL, overlay HTML |
| L2 | Bridge event hooks | Dashboard UI |
| L3 | MatchZy | Platform tournament bracket |
| L4 | CS2 dedicated server | Всё остальное |

**STP.Bridge** — anti-corruption layer на стороне игры (зеркало D5 в API).

---

## 8. Матрица домен → слой → артефакт

| Домен | L3 Domain | L2 Application | L1 Presentation | L4 Infra |
|-------|-----------|----------------|-----------------|----------|
| D1 Identity | `domain/identity/` | `AuthService` | `/auth/*`, WS auth | JWT, token repo |
| D2 Tournament | `domain/tournament/` | `TournamentService` | `/tournaments/*`, admin UI | BLOB repo |
| D3 Competition | `domain/competition/` | `CompetitionService` | bracket UI | bracket repo |
| D4 Match | `domain/match/` | `MatchService` | `/matches/*`, director UI | match repo |
| D5 Game | `domain/game_integration/` | `GameIntegrationService` | `/internal/cs2/*` | RCON, webhook parser |
| D6 Production | `domain/production/` | `ProductionService` | `/production/*`, agent WS | agent queue |
| D7 Overlay | `domain/overlay/` | `OverlayService` | overlay SPA, WS patch | WS broadcast |
| D8 Real-time | events only | `SignalingService` | WS channels | ws_hub, coturn |
| D9 Operations | audit types | `OperationsService` | health UI | audit repo |

### Вне Platform VPS

| Домен | Артефакт | Слои |
|-------|----------|------|
| D5 | `infra/game-server/plugins/STP.Bridge/` | L1–L2 on CS2 |
| D6,D8 | `apps/director-agent/` | L1–L4 local |
| D6 | OBS Studio | external |
| D7 | OBS Browser Source | external renderer |

---

## 9. Зависимости и правила импорта

### 9.1 Backend — разрешённый граф

```text
presentation  →  application  →  domain
                                    ↑
infrastructure ─────────────────────┘
(main.py wires infrastructure → domain ports → application)
```

| Из | В | Можно? |
|----|---|--------|
| `domain/` | `presentation/` | ❌ |
| `domain/` | `infrastructure/` | ❌ |
| `application/` | `domain/` | ✅ |
| `application/` | `infrastructure/` | ❌ (только ports из domain) |
| `infrastructure/` | `domain/` | ✅ (implements ports) |
| `presentation/` | `application/` | ✅ |

### 9.2 Зависимости между доменами (domain layer)

Домены **не импортируют друг друга напрямую** — только через:

1. **Shared kernel** — `domain/shared/value_objects.py` (`TeamId`, `MatchId`, `Score`)
2. **Domain events** — D5 публикует `GameRoundEnded`, D4 подписан в application layer
3. **Application orchestration** — `MatchService` координирует D4 + D5 + D7

```text
❌  domain/match/ imports domain/overlay/
✅  application/handlers/on_round_ended.py calls OverlayService
```

### 9.3 Frontend

```text
presentation → application → domain
infrastructure → application (через interfaces)
```

### 9.4 Agent ↔ Platform

```text
Agent application → Platform presentation (WS API)
Platform application → Agent presentation (WS commands)
```

Ни одна сторона не лезет в **domain другой стороны**.

---

## 10. Сквозные concerns

Проходят **вертикально** через все слои как middleware / decorators.

| Concern | L1 | L2 | L3 | L4 |
|---------|----|----|----|-----|
| **Auth** | middleware, token extract | `AuthService` verify | `Permission` VO | JWT, hash |
| **Transactions** | — | `@unit_of_work` | — | SQLAlchemy session |
| **Idempotency** | `Idempotency-Key` header | service check | — | webhook dedup table |
| **Audit** | actor from context | `OperationsService.log` | `AuditAction` enum | audit repo |
| **Validation** | Pydantic schemas | business rules | invariants in entities | — |
| **Errors** | HTTP exception handlers | map domain exceptions | `DomainError` hierarchy | — |

### Context propagation

```text
RequestContext:
  actor_type: organizer | director | judge | agent | system
  actor_id: str
  match_id: Optional[str]
  tournament_id: Optional[str]
```

Прокидывается L1 → L2 → audit (D9).

---

## 11. События между доменами

**Два класса:** domain events (в транзакции) · integration/side-effects (после commit через **MySQL outbox**).  
WS — ephemeral; business transition durable. См. [INVARIANTS.md §5](INVARIANTS.md#5-events-два-класса--outbox).

### 11.1 Каталог domain events

| Event | Publisher | Side effects (outbox handlers) |
|-------|-----------|--------------------------------|
| `TournamentPublished` | D2 | init bracket template |
| `MatchStarted` | D4 | D5 load, D6/D7 init |
| `GameRoundEnded` | D5 | D4 score, D7 snapshot |
| `MatchReviewRequested` | D4 | arm pause, banner, WS |
| `TechPauseStarted` | D4 | overlay/WS notify |
| `MatchForfeited` | D4 | D5, D3 advance, D7 |
| `MatchCompleted` | D4 | demo durable copy, revoke tokens |
| `ProductionDesiredChanged` | D6 | Agent reconcile |

### 11.2 Поток: round end → overlay

```text
webhook → normalize → UoW(update match + outbox)
  → commit → dispatcher → OverlayService.snapshot → WS overlay.snapshot
```

---

## Резюме: как читать платформу

```text
           ┌──────────────────────────────────────┐
           │  D2 Tournament  D3 Competition      │
           │         \         /                   │
           │          D4 Match (core)               │
           │         /    |    \                   │
           │   D5 Game  D6 Prod  D7 Overlay       │
           │         \    |    /                   │
           │     Realtime + Operations (caps)      │
           │  D1 Identity (сквозь всё)            │
           └──────────────────────────────────────┘
                         │
              4 слоя backend: Presentation → Application → Domain ← Infra
              Frontend: feature-oriented
              Runtime: desired/actual + outbox + snapshots + reconciliation
```

**Три физических runtime** (Platform API, CS2 VPS, Director Agent) — одна логическая модель.

---

## Связанные документы

- [INVARIANTS.md](INVARIANTS.md) — A1–A12, reconciliation  
- [ARCHITECTURE.md](ARCHITECTURE.md)  
- [TECH-STACK.md](TECH-STACK.md)  
- [overview/code-map.md](../overview/code-map.md)  

---

*v1.1 — после ревью: D8≠BC, outbox, state dimensions. Контракт структуры `apps/api/`.*
