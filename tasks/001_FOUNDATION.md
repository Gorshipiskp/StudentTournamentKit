# ТЗ 001 — Foundation (каркас платформы)

| Поле | Значение |
|------|----------|
| **Статус** | done (GATE 2026-08-11) |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer (+ devops на deploy skeleton) |
| **Этап roadmap** | 0 — Foundation |
| **Следующий** | TZ 002 — Game Slice |

---

## 0. Цель (для людей)

Поднять **рабочий каркас** Student Tournament Platform: репозиторий с приложениями, API с проверкой «жив / готов», Docker Compose, миграции БД и минимальный durable outbox — чтобы следующая волна (игровой сервер и матч) ставилась уже на готовый фундамент, а не в пустоту.

---

## 1. Scope

**В scope:**

- Структура монорепо: `apps/api/`, заготовки `apps/overlay|dashboard|judge|director-agent/`, `infra/platform/`, `infra/game-server/`, `scripts/`, `packages/api-types/` (заготовка)
- FastAPI: `/health`, `/ready`, middleware `correlation_id`
- Docker Compose: `api`, `nginx`, `mysql` (локальная/dev); `coturn` — stub/заготовка (можно не поднимать в GATE)
- SQLAlchemy 2 + Alembic: минимальные таблицы platform-owned state + `event_outbox`
- Слои backend по [docs/LAYERS.md](../docs/LAYERS.md): `presentation` / `application` / `domain` / `infrastructure`
- Один пример use-case, пишущий в outbox после commit + dispatcher stub (после commit / startup replay scan)
- `scripts/verify.ps1` (+ `.sh` опционально): lint/import-check + pytest smoke + compose config validate
- Обновить `overview/code-map.md` по факту путей

**Вне scope:**

- Живой CS2 / MatchZy / STP.Bridge (→ TZ002)
- Overlay UI, dashboard UI, Director Agent runtime
- Judge / WebRTC / OBS
- Публичный BestTvGU API
- Redis, K8s, multi-replica API
- Полный CRUD турниров/сеток (достаточно схемы таблиц + health)
- Прод-деплой на VPS организатора

---

## 2. Frozen (не менять без TL)

- **F1:** Stack — Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + MySQL 8 ([TECH-STACK.md](../docs/TECH-STACK.md), ADR-019)
- **F2:** Layout — 4 слоя backend; domain без FastAPI/SQLAlchemy/RCON ([LAYERS.md](../docs/LAYERS.md), A7)
- **F3:** MySQL = durable SoT **только** для platform-owned state ([INVARIANTS.md](../docs/INVARIANTS.md), ADR-025)
- **F4:** Side effects через **`event_outbox`** в той же транзакции, что aggregate; без Kafka/Redis (ADR-028)
- **F5:** API v1 = **single replica**; in-memory WS позже; Redis не вводить (ADR-031, A9)
- **F6:** Инварианты A1–A12 — architectural bug при нарушении ([INVARIANTS.md](../docs/INVARIANTS.md))
- **F7:** Секреты только в `.env` / `config/secrets/` — не в git, не в `workers/`
- **F8:** Коммиты только по @owner

---

## 3. To-be / UX

Для владельца после GATE:

1. `docker compose up` (или эквивалент) поднимает API + MySQL
2. `GET /health` → 200 без обращения к БД
3. `GET /ready` → 200 при живой MySQL
4. В ответе/логах есть `correlation_id` (или заголовок `X-Request-ID`)
5. `scripts/verify.ps1` проходит на чистой машине разработчика (с Docker)

---

## 4. Техника

| Слой | Пути |
|------|------|
| API | `apps/api/` |
| Compose | `infra/platform/docker-compose.yml` |
| Nginx | `infra/platform/nginx/` |
| Migrations | `apps/api/alembic/` |
| Verify | `scripts/verify.ps1` |
| Env schema | `.env.example` (без секретов) |
| Docs | `overview/code-map.md`, при необходимости `docs/ROADMAP.md` §0 |

**Минимальные таблицы (можно расширить полями из ARCHITECTURE, но не весь ER):**

- `tournaments` (минимум id, status, timestamps)
- `matches` (id, tournament_id, status, review_status, version, …)
- `event_outbox` (id, event_type, aggregate_*, payload, correlation_id, created_at, processed_at)
- опционально stub: `organizers`, `game_servers`

**Пример use-case для outbox:** например `CreateTournamentDraft` или `PingDomainEvent` — запись aggregate + outbox row в одном UoW; dispatcher помечает processed (может быть no-op handler).

---

## 5. Приёмка

- [x] Структура каталогов соответствует code-map / LAYERS
- [x] `GET /health` → 200, без DB
- [x] `GET /ready` → 200 при MySQL up; 503 если DB down
- [x] Alembic upgrade head на чистой MySQL
- [x] Outbox: после use-case есть строка; dispatcher обрабатывает / startup replay не падает
- [x] `correlation_id` / `X-Request-ID` в pipeline запроса
- [x] `.env.example` без секретов; `.gitignore` покрывает `.env`
- [x] `scripts/verify.ps1` зелёный
- [x] Owner smoke: compose up → health → ready → verify

---

## 6. Runbook

- `workers/developer/notes/TZ001-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ001-NEW-CHAT.md`
- Промптов: **M = 5** (P5 = GATE)

---

## 7. Паритет

Не применимо (нет multi-channel UI в этом ТЗ).

---

## Контекст для агента

Обязательно опираться на:

- [docs/INVARIANTS.md](../docs/INVARIANTS.md)
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) §6–8 (структура, data)
- [docs/LAYERS.md](../docs/LAYERS.md)
- [docs/TECH-STACK.md](../docs/TECH-STACK.md)
- [docs/DECISIONS.md](../docs/DECISIONS.md) ADR-019, 025, 028, 031
