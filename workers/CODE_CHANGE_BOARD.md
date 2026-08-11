# Доска изменений кода (CODE_CHANGE_BOARD)

> **Пишут:** все, кто менял код (developer, devops, …).  
> **Обрабатывает:** scout → `tech-overview/` → архив → очистка.  
> *Scout пока не развёрнут — записи накапливаются до появления роли.*

---

## Ожидают обработки

### 2026-08-11 — TZ001 P5 verify + GATE @developer

- **Пакеты:** `scripts/verify.ps1`, `scripts/verify.sh`, `docs/ROADMAP.md`, `tasks/001_FOUNDATION.md`
- **Суть:** GATE Foundation — verify зелёный, owner smoke, этап 0 отмечен
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P4 layers + outbox @developer

- **Пакеты:** `apps/api/app/{domain,application,infrastructure/outbox,presentation/...}`, probe router, tests
- **Суть:** CreateTournamentDraft в UoW + outbox dispatcher/startup replay + X-Request-ID
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P3 Alembic + /ready @developer

- **Пакеты:** `apps/api/alembic/`, `infrastructure/persistence/`, routers ready, Dockerfile CMD migrate
- **Суть:** таблицы foundation + readiness probe; health без DB
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P2 compose + env @developer

- **Пакеты:** `infra/platform/docker-compose.yml`, `nginx/`, `apps/api/Dockerfile`, `.env.example`, `overview/code-map.md`
- **Суть:** локальный стек api+mysql+nginx; `/health` через nginx и прямой порт
- **tech-overview:** systems/platform-deploy (когда появится)

### 2026-08-11 — TZ001 P1 monorepo + /health @developer

- **Пакеты:** `apps/api/`, stubs `apps/{overlay,dashboard,judge,director-agent}/`, `infra/{platform,game-server}/`, `packages/api-types/`, `overview/code-map.md`
- **Суть:** каркас monorepo; FastAPI `GET /health` без БД; pytest smoke
- **tech-overview:** systems/platform-api (когда появится)

---

## Формат записи

```markdown
### YYYY-MM-DD — <название> @developer

- **Пакеты:** …
- **Суть:** …
- **tech-overview:** …
```

Не писать: только markdown без кода · секреты · правки только workers/.
