# StudentTournamentKit — рекомендованный технологический стек

> Версия 1.0 · 2026-08-11 · статус: **recommended** (зафиксировано для разработки).  
> Связано: [ARCHITECTURE.md](ARCHITECTURE.md) · [DECISIONS.md](DECISIONS.md) · [VISION.md](VISION.md) · [INVARIANTS.md](INVARIANTS.md).

---

## Принципы выбора

1. **Надёжность live-event** важнее модных технологий.
2. **Минимум moving parts** на ноутбуке режиссёра (уже CS2 + OBS).
3. **Один язык/стек на слой** — проще для solo + агентов.
4. **Reuse** готовых tournament-решений для CS2 (MatchZy), не переписывать матчмейкинг.
5. **Переносимость:** Docker на платформе, portable binary на Windows, скрипты на VPS.

---

## Сводная таблица

| Слой | Технология | Версия (ориентир) |
|------|------------|-------------------|
| Backend API | **Python + FastAPI** | Python 3.12+, FastAPI 0.11x |
| ORM / миграции | **SQLAlchemy 2 + Alembic** | — |
| Валидация / схемы | **Pydantic v2** | — |
| Real-time (overlay, панели) | **WebSocket** (FastAPI + native browser WS) | single replica |
| Event durability | **MySQL `event_outbox`** + after-commit dispatcher | no Kafka/Redis v1 |
| Overlay WS | **`overlay.snapshot`** full state, per-match revision | not patch in v1 |
| База данных | **MySQL 8** | InnoDB, utf8mb4 |
| Кэш / pub-sub (опционально) | **Redis 7** | только при необходимости fanout |
| Frontend (все UI) | **Svelte 5 + Vite** | — |
| Dashboard / Judge | **SvelteKit** | routing, layouts |
| Overlay (OBS) | **Svelte + Vite** (SPA, без SSR) | минимальный bundle |
| Director Agent | **Go 1.22+** | один `.exe`, Windows service |
| OBS интеграция | **OBS Studio 30+**, **obs-websocket v5** | protocol 5.x |
| WebRTC (комментаторы) | **Pion WebRTC** (Go) + browser RTCPeerConnection | — |
| TURN/STUN | **coturn** | на Platform VPS |
| Захват видео для WebRTC | **OBS Virtual Camera** → FFmpeg (dshow) → Pion | Windows |
| Delayed Twitch | **OBS Stream Delay** (v1); FFmpeg в Agent — fallback v2 | v1 = OBS |
| CS2 сервер | **SteamCMD + CS2 Dedicated Server** | Linux |
| Мод-платформа | **Metamod:Source** | 1.12+ |
| Плагины CS2 | **CounterStrikeSharp** + **MatchZy** + **STK.Bridge** (свой) | .NET 8 |
| RCON | **aiorcon** (Python, async) | запасной канал команд |
| Reverse proxy | **nginx** | TLS, static, WS upgrade |
| Контейнеризация платформы | **Docker Compose** | api, nginx, coturn |
| CS2 deploy | **Bash + SteamCMD** (native, не Docker) | perf CS2 |
| CI / verify | **GitHub Actions** + `scripts/verify.ps1` | lint, test, build |
| Auth (организатор) | **JWT** (access) + refresh в MySQL | httpOnly cookie |
| Auth (роли на матч) | **Opaque invite tokens** в БД | revoke, scope, TTL |

---

## 1. Backend — Python + FastAPI

### Почему FastAPI, а не Node / Go

| Критерий | FastAPI | Node (Nest/Fastify) | Go |
|----------|---------|---------------------|-----|
| WebSocket + REST в одном процессе | Отлично | Отлично | Хорошо, больше boilerplate |
| Скорость разработки агентами | Высокая | Высокая | Средняя |
| Типизация / валидация | Pydantic из коробки | Zod/class-validator | struct tags |
| Экосистема RCON/скриптов | Python удобен для ops-скриптов | OK | OK |
| Один процесс на Platform VPS | Достаточно | Достаточно | Достаточно |

**Решение:** **FastAPI** — один сервис `apps/api/`, ASGI (uvicorn + uvicorn[standard]).

### Структура backend

```text
apps/api/
  app/
    main.py              # FastAPI app, lifespan
    api/                 # REST routers
    ws/                  # WebSocket handlers (overlay, dashboard, signaling)
    services/            # business logic
    adapters/
      cs2/               # CS2 adapter (MatchZy webhooks, RCON)
    models/              # SQLAlchemy models
    schemas/             # Pydantic DTO
    auth/
  alembic/
  tests/
  pyproject.toml         # uv или poetry
```

### Ключевые библиотеки (Python)

| Задача | Библиотека |
|--------|------------|
| HTTP client (к CS2 VPS) | `httpx` (async) |
| RCON | `aiorcon` |
| JWT | `python-jose` или `PyJWT` |
| Password hash | `argon2-cffi` |
| WebSocket | встроено в FastAPI / `websockets` |
| Background tasks | FastAPI BackgroundTasks → позже `arq` или Celery если нужно |
| File/BLOB | SQLAlchemy `LargeBinary` |

### Real-time

- **Overlay / dashboard / статусы:** WebSocket каналы per `match_id`; overlay = **full snapshot**.
- **WebRTC signaling:** WebSocket relay через Platform (не отдельный signaling server).
- **Outbox:** domain/side-effect events в MySQL; dispatcher после commit; startup replay.
- **Redis:** не в v1. **Constraint:** single API replica (ADR-031).
- **Correlation ID:** на всём пути Dashboard → API → CS2 → webhook → overlay.

---

## 2. Frontend — Svelte

### Разделение приложений

| App | Фреймворк | Зачем |
|-----|-----------|-------|
| `apps/overlay/` | **Svelte 5 + Vite** (SPA) | Минимальный размер, быстрый старт в OBS Browser Source |
| `apps/dashboard/` | **SvelteKit** | Организатор + режиссёр: routing, auth guards |
| `apps/judge/` | **SvelteKit** (или route group в dashboard) | Mobile-first layout |
| Commentator viewer | Route в overlay app: `/watch/[token]` | Один deploy, WebRTC player |

### UI и данные

| Задача | Технология |
|--------|------------|
| Стили | **Tailwind CSS 4** |
| API state | **@tanstack/svelte-query** |
| WS client | Тонкая обёртка над native `WebSocket` |
| Иконки | **lucide-svelte** |
| Формы | **sveltekit-superforms** + zod (опционально) |

### Сборка и деплой

- **pnpm workspace** в корне монорепо (`pnpm-workspace.yaml`).
- Production build → static files → **nginx** на Platform VPS.
- API proxy: `nginx` → `uvicorn:8000`, WS upgrade на том же домене (избегаем CORS в OBS).

### Overlay в OBS

- URL: `https://{platform}/overlay/{matchId}?token=...`
- Chromium Embedded (OBS Browser Source) — целевой движок; тестировать на CEF OBS 30+.
- Анимации: CSS transitions + Svelte transitions; без тяжёлого video в overlay.

---

## 3. Director Agent — Go

### Почему Go на Windows

| Критерий | Go | Electron | .NET |
|----------|-----|----------|------|
| Размер binary | ~15–25 MB | 150+ MB | ~50 MB + runtime |
| RAM на фоне CS2+OBS | Низкий | Высокий | Средний |
| WebRTC | **Pion** (зрелый) | node wrtc | SIPSorcery |
| Windows service | `kardianos/service` | Тяжело | Отлично |
| Portable exe | Да | Нет | Да |

**Решение:** `apps/director-agent/` — **Go 1.22+**, собирается в `stk-director-agent.exe`.

### Функции агента

```text
apps/director-agent/
  cmd/agent/main.go
  internal/
    obs/           # obs-websocket v5 client (github.com/andreykaipov/goobs или raw WS)
    webrtc/        # Pion publisher
    capture/       # FFmpeg subprocess: OBS Virtual Camera → raw frames (для WebRTC)
    platform/      # WS client к Platform API (auth, signaling, heartbeat)
    # delay/       # v2 only: FFmpeg Twitch delay branch (не в v1)
```

### OBS Virtual Camera → WebRTC

```text
OBS Program Output
  → OBS Virtual Camera (enabled)          # без задержки
  → FFmpeg (dshow, video=@device...) → raw/video pipe
  → Pion TrackLocalStaticSample
  → WebRTC → Commentators (browser)

OBS Stream Output
  → Stream Delay 90–120 s (OBS Advanced)  # только публичный эфир
  → Twitch RTMP
```

Аудио production в WebRTC **не передаём** — комментаторы слышат друг друга через Voicemeeter/Discord; в эфир аудио идёт через OBS → Twitch.

### OBS WebSocket v5

- Библиотека: прямой WebSocket JSON-RPC по [obs-websocket protocol 5](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md).
- Операции: `SetCurrentProgramScene`, `GetSceneList`, `SetInputSettings`, `TriggerHotkeyByName` (если нужно).
- Агент **не заменяет OBS** — только remote control из dashboard через platform → agent → OBS.
- **Stream Delay** в v1 настраивается в OBS (вручную или чек-лист из шаблона турнира); Agent не управляет delay в v1.

### Установка

- **Portable zip** + `stk-director-agent install` (Windows service, optional).
- Конфиг: `%AppData%/STK/agent.yaml` — platform URL, tournament token, OBS host/port/password.
- Мастер первого запуска: TUI или маленький Svelte page на `localhost:19876`.

---

## 4. Видео и аудио

### 4.1 Комментаторы (live, browser)

| Компонент | Технология |
|-----------|------------|
| Signaling | WebSocket через Platform API |
| Media | **WebRTC** (unidirectional: Agent → Commentator) |
| NAT traversal | **coturn** на Platform VPS (STUN + TURN) |
| Browser | `RTCPeerConnection` + `<video autoplay>` |
| Кол-во зрителей | 1–2 — **mesh/P2P** достаточно, SFU не нужен |

**Почему не HLS для комментаторов:** HLS даёт задержку 3–10+ с — неприемлемо.  
**Почему не WebRTC через платформу как SFU:** лишняя сложность; видео и так с ноутбука режиссёра.

### 4.2 Публичный Twitch (delayed)

| Этап | v1 (принято) | v2 (fallback) |
|------|--------------|---------------|
| Источник | OBS → Twitch RTMP | То же |
| Задержка | **OBS Stream Delay** (Настройки → Дополнительно → Задержка трансляции), ~90–120 с | **FFmpeg** buffer в Director Agent **или** SRS на Platform VPS |
| Live комментаторам | OBS Virtual Camera → Agent → WebRTC (**без** Stream Delay) | То же |
| Настройка | `broadcast_delay_seconds` в турнире = подсказка/чек-лист для OBS; не авто из Agent | Agent/API применяет delay автоматически |

**Почему OBS Stream Delay в v1:** штатная функция OBS; Virtual Camera остаётся без задержки; меньше процессов на ноутбуке (уже CS2 + OBS); проще для режиссёра с базовым опытом OBS.

**Когда переходить на FFmpeg в Agent:** если нужен контроль delay из панели без ручной настройки OBS, или OBS Stream Delay окажется недостаточным.

### 4.3 Аудио комментаторов

**Вне платформы:** Voicemeeter Banana / Potato → OBS audio mixer → Twitch.  
Платформа не трогает аудио-пайплайн в v1.

### 4.4 Захват игры (картинка в OBS)

| Источник | Когда |
|----------|-------|
| **CS2 fullscreen/window capture** в OBS | Режиссёр = оператор, CS2 на том же ПК |
| **GOTV auto-director** | Включён в CS2 spectator settings |
| **Hotkeys** | OBS или CS2 binds для override камеры |

---

## 5. CS2 — сервер и плагины

### Стек на CS2 VPS (Linux)

```text
SteamCMD
  └── CS2 Dedicated Server
        └── Metamod:Source 1.12+
              └── CounterStrikeSharp (.NET 8 runtime)
                    ├── MatchZy          # матчи, ready, knife, pause, demos
                    └── STK.Bridge       # наш плагин (см. ниже)
```

### Почему native, не Docker

CS2 чувствителен к CPU latency и tick; Docker добавляет слой и усложняет UDP.  
**Решение:** native install через `scripts/deploy-cs2.sh` на чистом Ubuntu 22.04/24.04.

### MatchZy

- Готовый tournament flow: match setup, team names, ready system, knife, sides, pause, demo recording.
- **Не переписываем** — оборачиваем API.
- Конфигурация матча через MatchZy JSON / console + наш adapter синхронизирует с Platform DB.

### STK.Bridge (свой CounterStrikeSharp плагин)

**Путь:** `infra/game-server/plugins/STK.Bridge/`

Задачи, которые MatchZy **не закрывает** или нужны кастомно:

| Функция | Описание |
|---------|----------|
| Webhook events → Platform | `round_start`, `round_end`, `player_death`, `bomb_planted`, `match_end`, `player_connect`, … |
| Judge pause timing | На `round_start` + `buy_phase`: если `review_requested` в API — `mp_pause_match` |
| Forfeit | По команде API — MatchZy/Console forfeit |
| Heartbeat | Ping platform каждые N секунд |
| GOTV | Убедиться что `tv_enable 1`, autorecord path в match metadata |

**Транспорт событий:** HTTP POST webhook на Platform API (primary).  
**Запасной:** RCON команды из Platform через `aiorcon` если webhook недоступен.

### Связка Platform ↔ CS2

```text
MatchZy / STK.Bridge (CSS)
    --HTTP webhook-->  Platform API  /api/internal/cs2/events
Platform API
    --HTTP-->  CS2 VPS : matchzy load/ready (если exposed)
    --RCON-->  CS2 : pause, unpause, forfeit (fallback)
Director laptop (GOTV)
    <--UDP/TCP-->  CS2 : spectator (не через Platform)
```

### RCON

- Библиотека: **`aiorcon`** (async, Python).
- Credentials: только на Platform VPS + CS2 VPS env, не в frontend.
- Rate limit и connection pool per server.

### Демо (GOTV)

- MatchZy / CS2: `tv_autorecord 1`, путь `{match_id}/{map}_{timestamp}.dem`.
- После `map_end`: STK.Bridge webhook → Platform сохраняет metadata; опционально `rsync`/`scp` script копирует на storage (v2).

---

## 6. База данных — MySQL 8

### Почему MySQL (уже решено)

- Постоянный VPS организатора, remote connection с Platform VPS.
- BLOB для логотипов/фонов (v1).

### Соглашения

| Параметр | Значение |
|----------|----------|
| Engine | InnoDB |
| Charset | utf8mb4_unicode_ci |
| Migrations | Alembic only, no manual drift |
| JSON columns | MySQL JSON для гибких настроек турнира |
| BLOB limit | Лого до 2 MB, фоны до 5 MB (soft limit в API) |

### Connection

- Platform VPS → MySQL VPS по TLS (`require_secure_transport=ON`).
- Pool: SQLAlchemy `pool_size=10`, `max_overflow=20`.
- **Owner (2026-08-11):** рабочая БД — удалённая managed MySQL (Timeweb Cloud, хост `*.twc1.net`). Подключение через корневой `.env` (`MYSQL_*`). Миграции Alembic до head `0006_demo_files` применены. Локальный MySQL в Compose — опционально (офлайн/CI). Детали: [infra/platform/README.md](../infra/platform/README.md).

---

## 7. Инфраструктура и деплой

### Platform VPS (Docker Compose)

```text
infra/platform/docker-compose.yml
  services:
    api:        # uvicorn, FastAPI
    nginx:      # TLS, static (Svelte builds), WS proxy
    coturn:     # TURN for WebRTC
```

### CS2 VPS (bash scripts)

```text
scripts/deploy-cs2.sh
  - install steamcmd, cs2
  - install metamod, counterstrikesharp
  - install matchzy, stk-bridge
  - configure firewall (game port, GOTV port)
  - register server in platform
```

### TLS

- **Let's Encrypt** (certbot) на nginx Platform VPS.
- OBS overlay **требует HTTPS** для WSS в Browser Source.

### Мониторинг (v1)

- Health endpoints: `/health`, `/health/ready` (DB ping).
- Dashboard widget: last heartbeat CS2, agent, overlay WS count.
- Без Prometheus в v1 — добавить на Production Ready.

---

## 8. Безопасность

| Область | Подход |
|---------|--------|
| Organizer auth | JWT short-lived + refresh rotation |
| Invite tokens | 32+ byte random, hashed in DB, scoped `role+match_id`, TTL |
| Internal webhooks CS2 | HMAC signature `X-STK-Signature` + shared secret per server |
| RCON | Firewall: only Platform VPS IP |
| Secrets | `config/secrets/` local, env on VPS, **не** в git/workers |
| CORS | Same-origin через nginx; overlay token auth |

---

## 9. Что сознательно не используем (v1)

| Технология | Почему нет |
|------------|------------|
| Kubernetes | Overkill для instance-per-organizer |
| mediasoup / LiveKit SFU | 1–2 комментатора — P2P + TURN достаточно |
| Electron | Тяжёлый Director Agent |
| Socket.io | Native WS проще |
| PostgreSQL | Решение владельца: MySQL |
| NDI для комментаторов | Нужен browser, не NDI client |
| Twitch API | Stream key manual |
| Redis (v1) | In-memory WS на одном процессе |
| CS2 в Docker | Perf и UDP |
| GraphQL | REST + WS достаточно |
| Multi-game adapter SDK | CS2-only |

---

## 10. Версии для фиксации в репо (pin при старте кода)

```yaml
# Рекомендация для .tool-versions / docs
python: "3.12"
nodejs: "22 LTS"
go: "1.22"
mysql: "8.0"
redis: "7"          # optional
obs: "30+"
obs-websocket: "5.x"
cs2_server: "latest via steamcmd"
metamod: "1.12+"
counterstrikesharp: "latest stable"
matchzy: "latest compatible with CSS"
```

---

## 11. Порядок внедрения по этапам ROADMAP

| Этап | Стек в фокусе |
|------|----------------|
| 1 Game Slice | FastAPI, MySQL, Alembic, SteamCMD, MatchZy, STK.Bridge, aiorcon |
| 2 Production Slice | Svelte overlay, SvelteKit dashboard, Go agent, obs-websocket, nginx |
| 3 People Slice | WebRTC Pion + coturn, judge SvelteKit, signaling WS |
| 4 Tournament Slice | SvelteKit admin wizard, JWT auth, invite tokens |
| 5 Broadcast Slice | OBS Stream Delay checklist, scene templates JSON; FFmpeg delay — только если понадобится |

---

## Связанные документы

- [ARCHITECTURE.md](ARCHITECTURE.md) — обновить §13 при расхождении
- [DECISIONS.md](DECISIONS.md) — ADR-019 … ADR-024
- [code-map.md](../overview/code-map.md)
