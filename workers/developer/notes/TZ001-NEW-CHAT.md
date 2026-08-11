# TZ001 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **только P1/5**.  
> Полный ранбук: [TZ001-PROMPT-RUNBOOK.md](TZ001-PROMPT-RUNBOOK.md) · ТЗ: [tasks/001_FOUNDATION.md](../../../tasks/001_FOUNDATION.md)

---

## P1/5 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (Student Tournament Platform).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · code-map § · IDENTITY · WORKLOG 3 дня · LAYERS § · INVARIANTS §A.
Skill: bestcs-tournaments-agent-start.

ТЗ: tasks/001_FOUNDATION.md — §0 · §1 · §2 Frozen · §4.
Промпт 1/5 — Каркас monorepo + FastAPI /health.

Делать:
- Структура apps/api (рабочий), заготовки apps/overlay|dashboard|judge|director-agent, infra/game-server, packages/api-types, infra/platform (под P2)
- FastAPI GET /health без DB
- pyproject + pytest smoke на /health
- Обновить overview/code-map.md

Не делать: Docker/MySQL/Alembic/outbox/CS2/UI; коммит без @owner.

DoD: uvicorn поднимает API; GET /health 200; pytest зелёный; каталоги на месте.

После: WORKLOG; трекер P1=done в workers/developer/notes/TZ001-PROMPT-RUNBOOK.md; остановись — P2 в новом чате.
```

---

## Однострочник владельца (последующие P)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/5 из TZ001-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## P2…P5

Тела — в [TZ001-PROMPT-RUNBOOK.md](TZ001-PROMPT-RUNBOOK.md).  
На P2+: онбординг **L0** — не читать AGENTS/ТЗ целиком; только § из карты P в ранбуке.
