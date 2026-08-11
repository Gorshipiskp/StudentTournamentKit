# Student Tournament Platform — code map

> Структура monorepo. Foundation **GATE** (TZ001): `/health`, Compose, Alembic/`/ready`, outbox, `scripts/verify.ps1`.

---

## Backend (`apps/api/`) — слои

> Спецификация: [docs/LAYERS.md](docs/LAYERS.md)

```text
presentation/   # L1 — routers, middleware (correlation_id)     ← done
application/    # L2 — commands, UnitOfWork port                ← done (P4)
domain/         # L3 — entities/events/ports (без SQLAlchemy)   ← done (P4)
infrastructure/ # L4 — persistence, outbox dispatcher           ← done (P3–P4)
```

**Entry:** `apps/api/app/main.py` · пакет: `apps/api/pyproject.toml` · тесты: `apps/api/tests/` · миграции: `apps/api/alembic/`.

| Эндпоинт | Назначение | Статус |
|----------|------------|--------|
| `GET /health` | Liveness, без БД | done (P1) |
| `GET /ready` | Readiness + MySQL | done (P3) |
| `POST /internal/foundation/probe` | CreateTournamentDraft + outbox | done (P4) |

## Домен → пути (presentation / deploy)

| Домен | Backend | Frontend / UI | Local / Infra | Статус |
|-------|---------|---------------|---------------|--------|
| Tournament & bracket | `apps/api/` | `apps/dashboard/` | — | skeleton |
| Teams & players | `apps/api/` | `apps/dashboard/` | — | skeleton |
| Match lifecycle | `apps/api/` + game adapter | `apps/dashboard/` | — | skeleton |
| Overlay | `apps/api/` (WS) | `apps/overlay/` | OBS Browser Source | skeleton |
| Director panel | `apps/api/` | `apps/dashboard/` | — | skeleton |
| Judge workflow | `apps/api/` | `apps/judge/` | mobile browser | skeleton |
| Commentator feed | `apps/api/` (signaling) | commentator route in overlay app | `apps/director-agent/` WebRTC | skeleton |
| OBS control | — | `apps/dashboard/` | `apps/director-agent/` → OBS WS | skeleton |
| CS2 game server | `apps/api/` adapter (позже) | — | `infra/game-server/`, `STP.Bridge` | skeleton |
| Platform deploy | — | — | `infra/platform/docker-compose.yml` | **working** (P2) |
| CS2 deploy | — | — | `scripts/deploy-cs2.*` | planned |
| Director install | — | — | `apps/director-agent/` installer | planned |
| Media (BLOB) | MySQL | served by API | persistent MySQL VPS | planned |
| Health / status | `apps/api/` → `presentation/.../health.py` | `apps/dashboard/` | — | `/health` done |
| Public API (BestTvGU) | `apps/api/public/` | — | — | later |

---

## Корень репозитория

| Путь | Назначение | Статус |
|------|------------|--------|
| `apps/api/` | Backend API + WebSocket | **working** (`/health`) |
| `apps/overlay/` | Broadcast overlay (Svelte) | README stub |
| `apps/dashboard/` | Director + organizer UI (Svelte) | README stub |
| `apps/judge/` | Judge UI (Svelte) | README stub |
| `apps/director-agent/` | Windows agent: OBS + WebRTC | README stub |
| `infra/platform/` | Docker Compose, nginx, coturn stub | **working** (api+mysql+nginx) |
| `infra/game-server/` | CS2 + plugins (`STP.Bridge`) | README stub |
| `packages/api-types/` | OpenAPI-generated types | README stub |
| `scripts/` | verify (+ later deploy-platform/cs2) | **working** (`verify.ps1`) |
| `tools/fake-cs2/` | Fake CS2: events + commands + snapshot | **working** (TZ002 P1) |
| `config/secrets/` | Секреты (gitignored) | planned |
| `docs/` | ARCHITECTURE, VISION, DECISIONS, ROADMAP | есть |
| `overview/` | Продуктовая документация | есть |
| `workers/` | Память ИИ-команды | есть |
| `tasks/` | ТЗ на фичи | есть |

---

## Внешние системы

| Система | Интеграция | Где в коде |
|---------|------------|------------|
| OBS Studio | WebSocket v5 | `apps/director-agent/` |
| MatchZy / CS2 | Plugin + RCON | `infra/game-server/`, adapter in `apps/api/` |
| MySQL | Persistent storage | `infra/platform/` (compose); migrations → P3 |
| Twitch | RTMP manual | вне кода (OBS) |
| TURN (coturn) | WebRTC | `infra/platform/` (stub / profile `webrtc`) |
| BestTvGU | Read API | `apps/api/public/` (later) |

### Порты platform (dev)

| Сервис | Хост | Примечание |
|--------|------|------------|
| nginx | `8080` | `/health`, `/api/` |
| api | `8000` | прямой uvicorn |
| mysql | `3307` | внутри сети всё ещё `3306` |

---

## Обновление

После кода: developer → CODE_CHANGE_BOARD → documentarian синхронизирует таблицу.
