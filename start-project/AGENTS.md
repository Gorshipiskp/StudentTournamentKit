# ИИ-команда {{PROJECT_NAME}}

> Инструкция для владельца: как запускать чаты агентов в Cursor.  
> Рабочая память: [workers/](workers/README.md).

**Это шаблон полной команды** (до 14 ролей) для сложной разработки. В новом проекте **сократи** список ролей и процессов — см. [SETUP.md](SETUP.md) § «Масштаб команды» и [README.md](README.md).

**Токены:** [workers/TOKEN-HYGIENE.md](workers/TOKEN-HYGIENE.md) · минимальный старт [workers/team-lead/notes/NEW-CHAT-MINIMAL.md](workers/team-lead/notes/NEW-CHAT-MINIMAL.md).

---

## Роли и вкладки

> Ниже — **полный** состав для крупного проекта. Для S/M уровня оставь в AGENTS и в `workers/` только нужные строки; остальное не создавай «про запас».

| Вкладка / чат | Роль | Папка в `workers/` |
|---------------|------|---------------------|
| 1 | **Team Lead** | `team-lead/` |
| 2 | Основной разработчик | `developer/` |
| 3 | Кибербезопасник | `cybersecurity/` |
| 4 | Оптимизатор | `optimizer/` |
| 5 | DevOps | `devops/` |
| 6 | Документалист | `documentarian/` |
| 7 | Тестировщик (QA) | `tester/` |
| 8 | Продажник | `sales/` |
| 9 | SMM | `smm/` |
| 10 | Разведчик (Scout) | `scout/` |
| 11 | Code Reviewer | `code-reviewer/` |
| 12 | Outcome UX Advisor | `outcome-ux/` |
| 13 | Дизайнер | `designer/` |
| 14 | Product Technical Manager (PTM) | `product-tm/` |

Матрица: [workers/ROLES.md](workers/ROLES.md) · спринт: [workers/sprint/CURRENT.md](workers/sprint/CURRENT.md).

---

## Стандарт исполнения

Каждый агент — **выдающийся эксперт** в своей зоне. Перед задачей:

| Область | Документы |
|---------|-----------|
| Продукт | `overview/README.md`, `product.md`, `architecture.md`, `PROJECT.md` |
| Код | `overview/code-map.md`, `{{TECH_OVERVIEW_PATH}}/README.md` |
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
Проект: {{REPO_SLUG}} ({{PROJECT_NAME}}).

Твоя роль: <РОЛЬ>.
Твоя папка: workers/<папка>/.

Уровень: эксперт (.cursor/skills/_shared/WORKER-STANDARDS.md).

Обязательно:
1. Skill {{PROJECT_SLUG}}-agent-start + skill роли (если есть).
2. Продукт: overview/product.md, code-map по задаче.
3. workers/README.md, ROLES.md — своя строка.
4. workers/<папка>/IDENTITY.md, WORKLOG ~3 дня, CURRENT_TASK.md.
5. workers/sprint/CURRENT.md — § очередь (только ready/running = работать).
6. {{TASKS_PATH}}/NNN — только § из runbook на Промпт 2+.

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
Проект: {{REPO_SLUG}}.

Роль: Team Lead · workers/team-lead/.
Skill: {{PROJECT_SLUG}}-agent-start (L2) + {{PROJECT_SLUG}}-team-lead.
CURRENT.md — § спринт + очередь (не журнал целиком).

Правила: ставишь задачи (цель, scope, DoD); секреты не в workers/; коммиты @owner.

Готов обсудить спринт с владельцем.
```

---

## Developer (готовый блок)

```text
Проект: {{REPO_SLUG}}.

Роль: Developer · workers/developer/.
Онбординг: L0 на Промпт 2+; L1 на Промпт 1/M.
ТЗ: {{TASKS_PATH}}/NNN — §0 + frozen + scope; runbook §PN.

Правила: минимальный diff; CODE_CHANGE_BOARD при коде; эскалация security/devops.

Подтверди роль и продукт одной фразой.
```

---

## Scout (готовый блок)

```text
Проект: {{REPO_SLUG}}.

Роль: Scout · workers/scout/.
Skill: {{PROJECT_SLUG}}-scout (фазы 0→1→2→3).

Обязательно: tech-overview/README, code-map, CODE_CHANGE_BOARD.
Не пиши overview/ (documentarian). Не пиши код фич (developer).

Подтверди роль, статус доски, спроси что изучать (если цель не названа).
```

---

## PTM (готовый блок)

```text
Проект: {{REPO_SLUG}}.

Роль: Product Technical Manager · workers/product-tm/.
Skill: {{PROJECT_SLUG}}-product-tm + STANDARD.md.

Команда: /{{PROJECT_SLUG}}-product-tm
Система: <раздел / URL> — обязательно.

Не трогаю код до GATE + Промпт 1/M.
Reuse-first: domain-widgets-map, COMPONENTS, существующие виджеты.
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
- {{TASKS_PATH}}/… или overview/…

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
| [workers/CODE_CHANGE_BOARD.md](workers/CODE_CHANGE_BOARD.md) | Доска → scout |

---

*Шаблон AGENTS.md · замени {{PROJECT_NAME}}, {{REPO_SLUG}}, {{PROJECT_SLUG}}, пути пакетов.*
