# StudentTournamentKit — code map

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
| `GET /api/v1/matches/{id}/overlay` | Overlay snapshot (`version`) | done (TZ003 P1) |
| `WS /ws/overlay/{matchId}` | Full `overlay.snapshot` fanout | done (TZ003 P1) |
| `POST .../overlay/override` | Manual overlay override | done (TZ003 P5) |
| `GET/PATCH .../production` | Desired/actual production | done (TZ003 P3) |
| `WS /ws/agent/{matchId}` | Agent desired push / actual | done (TZ003 P3) |
| `POST /api/v1/invites` (+ redeem/revoke) | Invite tokens + session | done (TZ004 P1) |
| `WS /ws/signaling/{matchId}` | WebRTC offer/answer/ICE relay | done (TZ004 P3) |
| `POST .../turn-credentials` | Ephemeral TURN (coturn) | done (TZ004 P3) |
| `WS /ws/judge/{matchId}` | Judge `match.status` fanout | done (TZ004 P6) |

## Домен → пути (presentation / deploy)

| Домен | Backend | Frontend / UI | Local / Infra | Статус |
|-------|---------|---------------|---------------|--------|
| Tournament & bracket | `apps/api/` | `apps/dashboard/` | — | skeleton |
| Teams & players | `apps/api/` | `apps/dashboard/` | — | skeleton |
| Match lifecycle | `apps/api/` + game adapter | `apps/dashboard/` | — | skeleton |
| Overlay | `apps/api/` (WS) | `apps/overlay/` | OBS Browser Source | **working** (TZ003 P1–P2) |
| Director panel | `apps/api/` | `apps/dashboard/` | — | **working** (TZ003 P5 `/director/`) |
| Judge workflow | `apps/api/` | `apps/judge/` | mobile browser | **working** (TZ004 P2 UI + P1 auth) |
| Commentator feed | `apps/api/` (signaling) | `apps/overlay` `/watch` | `apps/director-agent/` `--fake-webrtc` | **working** (TZ004 P3–P5) |
| OBS control | — | `apps/dashboard/` | `apps/director-agent/` → OBS WS | **working** (Agent; dashboard P5) |
| CS2 game server | `apps/api/` adapter (позже) | — | `infra/game-server/`, `STK.Bridge` | skeleton |
| Platform deploy | — | — | `infra/platform/docker-compose.yml` | **working** (P2) |
| CS2 deploy | — | — | `scripts/deploy-cs2.*` | planned |
| Director install | — | — | `apps/director-agent/` (+ `templates/` OBS stub) | **docs** (TZ003 P6; MSI later) |
| Media (BLOB) | MySQL | served by API | persistent MySQL VPS | planned |
| Health / status | `apps/api/` → `presentation/.../health.py` | `apps/dashboard/` | — | `/health` done |
| Public API (BestTvGU) | `apps/api/public/` | — | — | later |

---

## Корень репозитория

| Путь | Назначение | Статус |
|------|------------|--------|
| `apps/api/` | Backend API + WebSocket | **working** (`/health`) |
| `apps/overlay/` | Broadcast overlay (Svelte) | **working** (TZ003 P2 build) |
| `apps/dashboard/` | Director + organizer UI (Svelte) | **working** (TZ003 P5 director route) |
| `apps/judge/` | Judge UI (Svelte) | **working** (TZ004 P2 mobile SPA) |
| `apps/director-agent/` | Windows agent: OBS + WebRTC | **working** (TZ003 OBS; TZ004 `--fake-webrtc`) |
| `infra/platform/` | Docker Compose, nginx, coturn stub | **working** (api+mysql+nginx) |
| `infra/game-server/` | CS2 + plugins (`STK.Bridge`) | README stub |
| `packages/api-types/` | OpenAPI-generated types | README stub |
| `scripts/` | verify, **dev-remote** (remote MySQL dev), deploy-cs2 | **working** |
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
| MySQL | Persistent storage | Owner: remote managed (Timeweb); `.env` + Alembic head `0006`. Compose MySQL — optional. [infra/platform/README.md](../infra/platform/README.md) |
| Twitch | RTMP manual | вне кода (OBS) |
| TURN (coturn) | WebRTC | `infra/platform/` (stub / profile `webrtc`) |
| BestTvGU | Read API | `apps/api/public/` (later) |

### Порты и URL (dev)

| Сервис | Хост | URL / примечание |
|--------|------|------------------|
| nginx | `8080` | `http://127.0.0.1:8080` — `/health`, `/api/`, `/ws/`, `/overlay/`, `/director/` |
| api (прямой) | `8000` | `http://127.0.0.1:8000` — uvicorn; WS `/ws/overlay/{id}`, `/ws/agent/{id}` |
| mysql (publish) | `3307` | внутри compose сети `3306` |
| overlay (vite) | `5173` | `http://127.0.0.1:5173/overlay/{matchId}` |
| dashboard (vite) | `5174` | `http://127.0.0.1:5174/director/{matchId}` |
| judge (vite) | `5175` | `http://127.0.0.1:5175/?token=<invite>` |
| watch (overlay vite) | `5173` | `http://127.0.0.1:5173/watch?token=<invite>` (&mock=1) |
| OBS WebSocket | `4455` | только `apps/director-agent/` (A8); `--fake-obs` без OBS |
| Fake CS2 | `27099` | `tools/fake-cs2/` command listener (опционально) |

**Auth stub Agent:** query/header token = `STK_AGENT_TOKEN` (default `dev_agent_token_change_me`).

**OBS template:** [`apps/director-agent/templates/`](../apps/director-agent/templates/README.md) · pointer [`infra/platform/obs/`](../infra/platform/obs/README.md).

---

## Обновление

После кода: developer → CODE_CHANGE_BOARD → documentarian синхронизирует таблицу.
