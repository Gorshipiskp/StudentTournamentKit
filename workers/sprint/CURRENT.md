# Спринт S003

> Оркестратор: [ORCHESTRATOR.md](ORCHESTRATOR.md) · токены: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md)

---

## Активный спринт

| Поле | Значение |
|------|----------|
| **ID** | S003 |
| **Фокус** | TZ002 Game Slice — **primary GATE closed** (Fake); next TZ003 |
| **Начало** | 2026-08-11 |
| **Цель** | Primary GATE на Fake ✅; `live_smoke=blocked` (нет VPS / SSH @owner) |

---

## Сейчас открыть вкладки

1. `team-lead` — закрыть S003 / открыть TZ003 Production Slice
2. `tester` — primary smoke по `workers/developer/notes/TZ002-OWNER-SMOKE.md` (опционально)
3. `devops` — ждать VPS от @owner для live_smoke

---

## Очередь оркестратора

| slug | Задача | Зависит от | Статус |
|------|--------|------------|--------|
| team-lead | Закрыть TZ001; открыть TZ002 ранбук | — | done |
| developer | TZ002 P1–P8 GATE | team-lead | **done** |
| devops | deploy-cs2 / VPS когда @owner даст доступ | developer P7 | pending (`live_smoke=blocked`) |
| tester | Primary smoke после P8 | developer GATE | ready |

---

## Журнал (новые сверху)

```text
2026-08-11 developer: TZ002 P8 GATE done — failure A–E; verify.ps1 [1–4]; live_smoke=blocked; primary GATE closed Fake
2026-08-11 developer: TZ002 P7 done — deploy-cs2 dry-run + demo_files durable; next P8 GATE (новый чат)
2026-08-11 developer: TZ002 P6 done — STP.Bridge skeleton; build blocked (no dotnet); next P7 deploy (новый чат)
2026-08-11 developer: TZ002 P5 done — game_servers + assign + snapshot reconcile; next P6 Bridge (новый чат)
2026-08-11 developer: TZ002 P4 done — judge review→pause→continue/forfeit; next P5 registry (новый чат)
2026-08-11 developer: TZ002 P3 done — pause/resume/forfeit + command_id/ack; next P4 judge (новый чат)
2026-08-11 developer: TZ002 P2 done — ingest HMAC + Match FSM + GET score; next P3 commands (новый чат)
2026-08-11 developer: TZ002 P1 done — CONTRACT + fake-cs2 self-test/pytest; next P2 ingest (новый чат)
2026-08-11 team-lead: S003 — TZ001 closed; TZ002 Game Slice runbook M=8; developer ready P1
2026-08-11 developer: TZ001 GATE готов — verify.ps1 OK; owner smoke OK; этап 0 закрыт
2026-08-11 developer: TZ001 P4 done — layers+UoW+outbox+correlation; next P5 GATE
2026-08-11 developer: TZ001 P3 done — Alembic + /ready; next P4 outbox/layers
2026-08-11 developer: TZ001 P2 done — compose api+mysql+nginx; next P3
2026-08-11 developer: TZ001 P1 done — monorepo + /health + pytest; next P2
2026-08-11 team-lead: TZ001 Foundation + PROMPT-RUNBOOK M=5
```

---

*Журнал: max 60 записей → sprint/archive/*
