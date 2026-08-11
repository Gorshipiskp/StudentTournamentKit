# TZ001 — PROMPT RUNBOOK · Foundation

> ТЗ: [tasks/001_FOUNDATION.md](../../../tasks/001_FOUNDATION.md)  
> Философия: минимум промптов → максимум автономии · 1 чат = 1 `Промпт N/M`  
> **M = 5** · последний = GATE

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/5 | Каркас monorepo + FastAPI `/health` | done | 2026-08-11 |
| 2/5 | Docker Compose (api, nginx, mysql) + env schema | done | 2026-08-11 |
| 3/5 | Alembic + таблицы + `/ready` | done | 2026-08-11 |
| 4/5 | Слои domain/app/infra + UoW + outbox + correlation_id | done | 2026-08-11 |
| 5/5 | verify + GATE / owner smoke | done | 2026-08-11 |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать из ТЗ |
|---|--------------|
| 1/5 | §0 + §1 + §2 Frozen + §4 (пути) |
| 2/5 | §1 Compose · §2 F7 · §4 Compose/nginx/env |
| 3/5 | §4 таблицы · §2 F3 · §5 ready/alembic |
| 4/5 | §2 F2 F4 F6 · §4 use-case/outbox · LAYERS + INVARIANTS |
| 5/5 | §3 To-be · §5 Приёмка целиком |

---

## P1/5 — Каркас monorepo + FastAPI health

### Делать

- Создать структуру:
  - `apps/api/` (рабочий пакет)
  - заготовки-README (не пустые заглушки без смысла): `apps/overlay/`, `apps/dashboard/`, `apps/judge/`, `apps/director-agent/`, `infra/game-server/`, `packages/api-types/`
  - `infra/platform/` (под compose в P2)
- FastAPI app: `GET /health` → `{"status":"ok"}` **без** обращения к БД
- `pyproject.toml` / зависимости: fastapi, uvicorn; pytest smoke на `/health`
- Entry: `apps/api/app/main.py` (или эквивалент)
- Кратко обновить `overview/code-map.md` (появившиеся пути)

### Не делать

- Docker Compose (P2)
- MySQL / Alembic (P3)
- Outbox / доменная логика (P4)
- CS2, UI, Agent
- Коммит без @owner

### DoD

- [x] `uvicorn` (или `python -m`) поднимает API локально
- [x] `GET /health` → 200
- [x] pytest smoke зелёный
- [x] Каталоги из scope существуют с README-назначением

### Проверки

```text
pytest apps/api/tests -q  # или согласованный путь
curl/http GET /health
```

### После P

- WORKLOG developer 1–3 строки
- Трекер: P1 → done
- Новый чат на P2 (не продолжать этот)

---

## P2/5 — Docker Compose + env schema

### Делать

- `infra/platform/docker-compose.yml`: сервисы **api**, **mysql:8**, **nginx** (proxy на api; static later)
- `coturn` — закомментированный stub или profile `webrtc` (не обязателен для GATE)
- `.env.example`: `MYSQL_*`, `API_*`, без реальных паролей
- Dockerfile для api (простой, multi-stage ок)
- nginx: `/health` и `/api/` → api; заготовка под static
- Документировать в `infra/platform/README.md`: как `compose up`, какие порты

### Не делать

- Alembic/миграции (P3) — MySQL пустой ок
- Outbox logic
- Прод TLS / Let's Encrypt (достаточно http localhost)
- Redis

### DoD

- [x] `docker compose -f infra/platform/docker-compose.yml config` валиден
- [x] `compose up` поднимает api+mysql+nginx
- [x] С хоста: health через nginx или прямой порт api
- [x] `.env.example` в git; `.env` в gitignore

### Проверки

```text
docker compose -f infra/platform/docker-compose.yml config
docker compose -f infra/platform/docker-compose.yml up -d --build
# GET /health
```

---

## P3/5 — Alembic + таблицы + /ready

### Делать

- SQLAlchemy 2 models + Alembic
- Миграция `head`: минимум `tournaments`, `matches` (поля `status`, `review_status`, `version`), `event_outbox`
- `GET /ready`: проверка соединения с MySQL → 200 / 503
- `/health` по-прежнему **без** DB
- Compose: api ждёт healthy mysql (healthcheck)

### Не делать

- Полный ER из ARCHITECTURE (достаточно минимума для Foundation)
- Outbox dispatcher (P4)
- CRUD HTTP для турниров (кроме того, что нужно для ready)

### DoD

- [x] На чистой MySQL: `alembic upgrade head` успешен
- [x] `/ready` → 200 при DB up
- [x] Стоп mysql → `/ready` → 503; `/health` → 200
- [x] Тест(ы) на ready/health разделение

### Проверки

```text
alembic upgrade head
GET /health  → 200
GET /ready   → 200
```

---

## P4/5 — Слои + UoW + outbox + correlation_id

### Делать

- Разложить `apps/api/app/` по LAYERS:
  - `presentation/` (routers, middleware)
  - `application/` (services / use cases, unit_of_work)
  - `domain/` (минимум entities/events ports — без SQLAlchemy)
  - `infrastructure/` (persistence, outbox dispatcher)
- Middleware: принять/сгенерировать `X-Request-ID` / `correlation_id`, прокинуть в контекст
- Use-case (например create tournament draft **или** явный `RecordFoundationProbe`):
  - в одной транзакции: запись aggregate + строка `event_outbox`
  - после commit — dispatcher обрабатывает (handler может логировать no-op)
- Startup: scan `processed_at IS NULL` → replay (идемпотентно)
- Соблюсти F2/F4/F6: domain не импортирует FastAPI/SQLAlchemy

### Не делать

- WebSocket hub (можно заготовку комментарием)
- CS2 adapter / webhooks HMAC (TZ002)
- Overlay / frontend apps

### DoD

- [x] Структура каталогов соответствует LAYERS
- [x] Use-case создаёт outbox row; после dispatch `processed_at` заполнен
- [x] Restart API с необработанной outbox → replay без падения
- [x] Запрос с/без `X-Request-ID` работает; id попадает в outbox или логи
- [x] Pytest на UoW+outbox (можно на testcontainers или compose mysql)

### Проверки

```text
# вызвать use-case (HTTP или service test)
# SELECT * FROM event_outbox
# restart api → unprocessed drained
```

---

## P5/5 — verify + GATE

### Делать

- `scripts/verify.ps1`:
  - проверить compose config
  - pytest
  - (опционально) ruff/mypy если уже подключены — не раздувать scope
- Пройти чеклист §5 ТЗ сам
- Обновить `docs/ROADMAP.md` § Этап 0 — отметить выполненное
- WORKLOG + журнал CURRENT.md
- Краткий отчёт владельцу: как поднять, как smoke

### Не делать

- Начинать TZ002 в этом чате
- Коммит без @owner
- «Улучшения» вне §5

### DoD (GATE)

- [x] Все пункты §5 ТЗ
- [x] Owner smoke из §3 выполним по инструкции ≤ 10 минут
- [x] Трекер: все P done
- [x] Явно: «TZ001 GATE готов» / блокеры

### Owner smoke (чеклист)

```text
1. cp .env.example .env  (пароли локальные)
2. docker compose -f infra/platform/docker-compose.yml up -d --build
3. alembic upgrade head  (если не на старте контейнера)
4. GET /health → 200
5. GET /ready → 200
6. scripts/verify.ps1 → OK
7. (если есть) вызвать probe/create-draft → outbox row processed
```

---

## Эскалация

| Ситуация | Куда |
|----------|------|
| Нужен живой CS2 | Не в этом ТЗ → TL / TZ002 |
| Конфликт Frozen | @team-lead |
| Compose не стартует на Windows | @devops / документ workaround |
| Хочется Redis «на будущее» | Отклонить (F5) |

---

## Связь со следующей волной

После GATE → **TZ002 Game Slice**: Fake CS2 + real Bridge contract + MatchZy deploy scripts + pause/forfeit.  
Foundation уже даёт: MySQL, outbox, correlation_id, `/ready`, слои API.
