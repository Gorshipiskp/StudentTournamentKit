# Спринт S002

> Оркестратор: [ORCHESTRATOR.md](ORCHESTRATOR.md) · токены: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md)

---

## Активный спринт

| Поле | Значение |
|------|----------|
| **ID** | S002 |
| **Фокус** | TZ001 Foundation — каркас API + Compose + outbox |
| **Начало** | 2026-08-11 |
| **Цель** | Закрыть GATE TZ001, затем TZ002 Game Slice |

---

## Сейчас открыть вкладки

1. `team-lead` — закрыть S002 / открыть TZ002 Game Slice (по решению владельца)
2. `tester` — optional owner smoke confirm (pending → ready после TL)

---

## Очередь оркестратора

| slug | Задача | Зависит от | Статус |
|------|--------|------------|--------|
| documentarian | VISION…INVARIANTS | — | done |
| team-lead | ТЗ001 + ранбук Foundation | documentarian | done |
| developer | TZ001 Foundation GATE | team-lead | done |
| devops | Поддержка compose при блокере | developer | skipped |
| tester | Owner smoke / verify после P5 | developer P5 | ready |

Статусы: `pending` · `ready` · `running` · `done` · `blocked` · `skipped`

---

## Журнал (новые сверху)

```text
2026-08-11 developer: TZ001 GATE готов — verify.ps1 OK; owner smoke OK; этап 0 закрыт
2026-08-11 developer: TZ001 P4 done — layers+UoW+outbox+correlation; next P5 GATE
2026-08-11 developer: TZ001 P3 done — Alembic + /ready; next P4 outbox/layers
2026-08-11 developer: TZ001 P2 done — compose api+mysql+nginx; health via :8080/:8000; next P3
2026-08-11 developer: TZ001 P1 done — monorepo + /health + pytest; next P2 compose
2026-08-11 team-lead: TZ001 Foundation + PROMPT-RUNBOOK M=5; developer ready P1
2026-08-11 documentarian: INVARIANTS + ADR-025…036 (P0/P1 ревью); ARCHITECTURE v2.1
2026-08-11 documentarian: зафиксировано видение — VISION, ARCHITECTURE, DECISIONS, ROADMAP, overview/*
2026-08-11 team-lead: закрыт bootstrap S001, открыт S002 Foundation→Game Slice
```

---

*Журнал: max 60 записей → sprint/archive/*
