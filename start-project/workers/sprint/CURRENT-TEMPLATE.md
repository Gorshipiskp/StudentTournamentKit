# Спринт {{SPRINT_ID}}

> Оркестратор: [ORCHESTRATOR.md](ORCHESTRATOR.md) · токены: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md)

---

## Активный спринт

| Поле | Значение |
|------|----------|
| **ID** | {{SPRINT_ID}} |
| **Фокус** | Bootstrap ИИ-команды + черновик overview |
| **Начало** | YYYY-MM-DD |
| **Цель** | Одна фраза для владельца |

---

## Сейчас открыть вкладки

1. `team-lead` — приоритеты
2. `scout` — code-map + tech-overview каркас
3. `documentarian` — overview черновики

---

## Очередь оркестратора

| slug | Задача | Зависит от | Статус |
|------|--------|------------|--------|
| team-lead | Утвердить структуру workers + первый фокус | — | ready |
| scout | code-map AS-IS, tech-overview README | — | ready |
| documentarian | product.md + architecture черновик | scout | pending |
| developer | — | team-lead | pending |

Статусы: `pending` · `ready` · `running` · `done` · `blocked` · `skipped`

---

## Журнал (новые сверху)

```text
YYYY-MM-DD team-lead: создан спринт bootstrap
```

---

*Журнал: max 60 записей → sprint/archive/*
