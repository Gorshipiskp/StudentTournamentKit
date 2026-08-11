# NEW-CHAT — минимальный старт

> Полные промпты — [AGENTS.md](../../AGENTS.md). Канон: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md).

---

## L0 — Промпт 2+ / smoke

```text
Проект: {{REPO_SLUG}}.

Роль: <РОЛЬ> · workers/<папка>/.
Онбординг: L0 — не читать AGENTS/tasks/README целиком.

Задача: CURRENT_TASK + tasks/<NNN> §<…> + runbook §PN.
Правила: WORKER-STANDARDS · секреты не в чат · коммит @owner.

<одна фраза задачи>
```

---

## L1 — Промпт 1/M

```text
Проект: {{REPO_SLUG}}.

Роль: <РОЛЬ> · workers/<папка>/.
Онбординг: L1 — product § · code-map § · IDENTITY · WORKLOG 3 дня.
ТЗ: tasks/<NNN> — §0 · frozen · scope P1.

Промпт 1/M — <цель>
```

---

## L2 — Team Lead

```text
Проект: {{REPO_SLUG}}.

Роль: Team Lead · workers/team-lead/.
CURRENT — § спринт + очередь (не журнал).

Готов обсудить спринт.
```

---

## Однострочник владельца

```text
Очередь: workers/sprint/CURRENT.md — строка `<slug>`. Выполни, обнови статус и журнал.
```
