# CURRENT_TASK

| Поле | Значение |
|------|----------|
| **ID** | TZ002 |
| **От** | @team-lead |
| **Статус** | **done** (primary GATE) |
| **Исполнитель** | workers/developer/ |

## Цель

Game Slice: контракт CS2 ↔ Platform, Fake Game Server, match/judge/commands, скелет STK.Bridge + deploy scripts — GATE по tasks/002_GAME-SLICE.md.

## Scope

**Делать:**

- Промпты 1…M по `workers/developer/notes/TZ002-PROMPT-RUNBOOK.md`
- 1 чат = 1 промпт

**Не трогать:**

- Overlay UI / Director Agent / WebRTC / OBS (TZ003+)
- Коммиты без @owner
- Live VPS без явного доступа владельца (live smoke — optional / blocked)

## Критерии готовности

- [x] Все P done в трекере ранбука
- [x] §5 ТЗ 002 (primary GATE на Fake)
- [x] Live 5v5 — documented `live_smoke=blocked` (нет VPS)

## Контекст

- `tasks/002_GAME-SLICE.md`
- `workers/developer/notes/TZ002-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ002-OWNER-SMOKE.md`
- `docs/INVARIANTS.md`, `docs/ARCHITECTURE.md` §10–11

## Журнал задачи

| Дата | Запись |
|------|--------|
| 2026-08-11 | TZ002 P8 GATE done — A–E + verify; live_smoke=blocked; стоп → TZ003 / @owner commit |
| 2026-08-11 | TZ002 P7 done — deploy-cs2 + durable demo; next P8 GATE (новый чат) |
| 2026-08-11 | TZ002 P6 done — Bridge skeleton + build blocker; next P7 deploy (новый чат) |
| 2026-08-11 | TZ002 P5 done — registry + reconcile; next P6 Bridge (новый чат) |
| 2026-08-11 | TZ002 P4 done — judge review E2E Fake; next P5 registry (новый чат) |
| 2026-08-11 | TZ002 P3 done — commands + ack/desired-actual; next P4 judge (новый чат) |
| 2026-08-11 | TZ002 P2 done — ingest HMAC + Match FSM; next P3 commands (новый чат) |
| 2026-08-11 | TZ002 P1 done — CONTRACT + fake-cs2; next P2 ingest/FSM (новый чат) |
| 2026-08-11 | TZ001 закрыт; старт TZ002 |
