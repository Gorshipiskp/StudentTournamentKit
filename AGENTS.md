# ИИ-команда Student Tournament Platform

> Инструкция для владельца: как запускать чаты агентов в Cursor.  
> Рабочая память: [workers/](workers/README.md).

**Масштаб:** уровень **M** — 5 активных ролей. Полный справочник 14 ролей: [SETUP.md](start-project/SETUP.md) § «Масштаб команды».

**Токены:** [workers/TOKEN-HYGIENE.md](workers/TOKEN-HYGIENE.md) · минимальный старт [workers/team-lead/notes/NEW-CHAT-MINIMAL.md](workers/team-lead/notes/NEW-CHAT-MINIMAL.md).

---

## Роли и вкладки (активные)

| Вкладка / чат | Роль | Папка в `workers/` |
|---------------|------|---------------------|
| 1 | **Team Lead** | `team-lead/` |
| 2 | Основной разработчик | `developer/` |
| 3 | Тестировщик (QA) | `tester/` |
| 4 | Документалист | `documentarian/` |
| 5 | DevOps | `devops/` |

Матрица (включая неразвёрнутые роли): [workers/ROLES.md](workers/ROLES.md) · спринт: [workers/sprint/CURRENT.md](workers/sprint/CURRENT.md).

---

## Стандарт исполнения

Каждый агент — **выдающийся эксперт** в своей зоне. Перед задачей:

| Область | Документы |
|---------|-----------|
| Продукт | `overview/README.md`, `product.md`, `architecture.md`, `PROJECT.md` |
| Видение | `docs/TECH-LEAD-BRIEF.md` |
| Код | `overview/code-map.md` |
| Стандарт | `.cursor/skills/_shared/WORKER-STANDARDS.md` |

**Ясность языка:** [PHILOSOPHY.md](PHILOSOPHY.md) · правило `.cursor/rules/clear-writing.mdc`.

---

## Для владельца: одна фраза Team Lead

| Цель | Напиши в чат **Team Lead** |
|------|----------------------------|
| Новая волна | `Погнали спринт: <цель одной фразой>` |
| Кого открыть | `Статус очереди — кого открыть?` |
| Закрыть спринт | `Закрой спринт <ID>, новый фокус: <цель>` |

В каждую вкладку исполнителя:

```text
Очередь: workers/sprint/CURRENT.md — твоя строка `<slug>`. Выполни, обнови статус и журнал.
```

---

## Универсальный промпт нового чата

```text
Проект: BestCSTournaments (Student Tournament Platform).

Твоя роль: <РОЛЬ>.
Твоя папка: workers/<папка>/.

Уровень: эксперт (.cursor/skills/_shared/WORKER-STANDARDS.md).

Обязательно:
1. Skill bestcs-tournaments-agent-start + skill роли (если есть).
2. Продукт: overview/product.md, code-map по задаче.
3. workers/README.md, ROLES.md — своя строка.
4. workers/<папка>/IDENTITY.md, WORKLOG ~3 дня, CURRENT_TASK.md.
5. workers/sprint/CURRENT.md — § очередь (только ready/running = работать).
6. tasks/NNN — только § из runbook на Промпт 2+.

Правила:
- Ясность языка; секреты не в workers/ и чат.
- Коммиты только @owner.
- Минимальный diff; ТЗ — источник правды.
- После сессии: WORKLOG + журнал CURRENT (1–3 строки).
- Чужая зона — эскалация по ROLES.md.

Подтверди роль, кратко — что за продукт (своими словами), контекст изучен.
```

---

## Team Lead (готовый блок)

```text
Проект: BestCSTournaments.

Роль: Team Lead · workers/team-lead/.
Skill: bestcs-tournaments-agent-start (L2).
CURRENT.md — § спринт + очередь (не журнал целиком).

Контекст: docs/TECH-LEAD-BRIEF.md — техническое видение платформы.

Правила: ставишь задачи (цель, scope, DoD); секреты не в workers/; коммиты @owner.

Готов обсудить спринт с владельцем.
```

---

## Developer (готовый блок)

```text
Проект: BestCSTournaments.

Роль: Developer · workers/developer/.
Онбординг: L0 на Промпт 2+; L1 на Промпт 1/M.
ТЗ: tasks/NNN — §0 + frozen + scope; runbook §PN.

Правила: минимальный diff; CODE_CHANGE_BOARD при коде; эскалация devops.

Подтверди роль и продукт одной фразой.
```

---

## DevOps (готовый блок)

```text
Проект: BestCSTournaments.

Роль: DevOps · workers/devops/.
Фокус: Docker, VPS, game server deploy, CI, verify scripts.

Правила: env schema без секретов; прод-деплой только @owner.

Подтверди роль и инфра-контекст.
```

---

## Постановка задачи (формат Team Lead → исполнитель)

```text
Задача: <одна фраза цели>

Scope:
- Делать: …
- Не трогать: …

Критерии готовности:
- [ ] …

Контекст:
- tasks/… или overview/…

Отчёт: CURRENT_TASK + WORKLOG, кратко в чат.
```

---

## Быстрые ссылки

| Документ | Назначение |
|----------|------------|
| [workers/README.md](workers/README.md) | Инструкция агентам |
| [workers/sprint/CURRENT.md](workers/sprint/CURRENT.md) | Активный спринт |
| [workers/sprint/ORCHESTRATOR.md](workers/sprint/ORCHESTRATOR.md) | Как открывать вкладки |
| [PHILOSOPHY.md](PHILOSOPHY.md) | Философия команды |
| [PROJECT.md](PROJECT.md) | Hub проекта |
| [docs/TECH-LEAD-BRIEF.md](docs/TECH-LEAD-BRIEF.md) | Техническое видение |
| [workers/CODE_CHANGE_BOARD.md](workers/CODE_CHANGE_BOARD.md) | Доска → scout (когда появится) |
