# Bootstrap: развернуть ИИ-команду в новом проекте

> Выполняет **агент** по запросу владельца или **владелец** вручную.  
> После bootstrap папку `start-project/` можно оставить как архив или удалить — рабочие файлы живут в корне.

---

## Профиль проекта (заполнить первым)

```yaml
project_name: "{{PROJECT_NAME}}"
repo_slug: "{{REPO_SLUG}}"
owner: "<имя владельца>"
primary_stack: "<например: SvelteKit + FastAPI + PostgreSQL>"
packages:
  - path: "{{MAIN_APP_PATH}}"
    role: frontend
  - path: "{{BACKEND_PATH}}"
    role: backend
  # добавь: mobile/, bot/, infra/
secrets_location: "<например: config/secrets/ — НЕ в workers/>"
verify_command: "<например: ./scripts/verify.ps1 или npm test>"
```

---

## Масштаб команды (выбрать с владельцем)

Не копируй «всё подряд». Набор описывает **максимальный** процесс; реальный проект редко нуждается во всех 14 ролях.

| Уровень | Когда | Роли (минимум) | Документация | Процессы |
|---------|-------|----------------|--------------|----------|
| **S** — лёгкий | скрипт, лендинг, прототип, 1 разработчик | `developer` (+ опционально `team-lead` как «координатор в одном чате») | `PROJECT.md`, краткий README | без sprint-очереди; WORKLOG по желанию |
| **M** — продукт | приложение с релизами, 2–3 зоны ответственности | + `tester`, `documentarian` | + `overview/`, `tasks/` | упрощённый `sprint/CURRENT` или без оркестратора |
| **L** — платформа | монорепо, multi-channel, долгие эпики | полный [ROLES.md](workers/ROLES.md) | + `tech-overview/`, scout | TOKEN-HYGIENE, runbook N/M, CODE_CHANGE_BOARD, PTM/designer по необходимости |

**Правило:** если сомневаешься — начни с **S** или **M** и расширяй, когда появится боль (не наоборот).

Примеры **можно не разворачивать** в простом проекте:

- `scout/` + `tech-overview/` — пока код маленький и один человек держит контекст в голове
- `product-tm/`, `designer/`, `outcome-ux/` — пока нет отдельной дизайн-системы и экранных эталонов
- `sales/`, `smm/` — пока нет коммерции и публичного контента
- Оркестратор с 8 вкладками — пока владелец работает в 1–2 чатах
- Runbook на 10 промптов — для задач, которые закрываются одним чатом

Зафиксируй выбор в `workers/sprint/CURRENT.md` или в `PROJECT.md` § «Команда».

---

## Шаг 1 — Каркас папок

Создай по [docs/PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md) **с учётом уровня S/M/L** (см. § «Масштаб команды»):

- `workers/` + подпапки **только нужных** ролей из [workers/ROLES.md](workers/ROLES.md)
- `workers/sprint/` + `workers/sprint/archive/`
- `overview/` — product, architecture, code-map (черновики)
- `{{TECH_OVERVIEW_PATH}}/` — README + заготовки systems/
- `{{TASKS_PATH}}/` — README + шаблон ТЗ
- `PROJECT.md` — hub в корне
- `.cursor/skills/` + `.cursor/rules/`

---

## Шаг 2 — Перенос workers

1. Скопируй `start-project/workers/README.md` → `workers/README.md`
2. `ROLES.md`, `TOKEN-HYGIENE.md`, `IDEAS.md`, `CODE_CHANGE_BOARD.md`
3. `sprint/ORCHESTRATOR.md`, `sprint/CURRENT.md` из `CURRENT-TEMPLATE.md`
4. Для **каждой выбранной** роли из ROLES (не обязательно все 14):
   - `workers/<slug>/IDENTITY.md` — из `workers/roles/<slug>/IDENTITY.md`
   - `workers/<slug>/WORKLOG.md` — из `_templates/WORKLOG.md`
5. `workers/team-lead/notes/NEW-CHAT-MINIMAL.md` — скопировать из start-project

---

## Шаг 3 — Cursor

1. `.cursor/skills/_shared/WORKER-STANDARDS.md`
2. `.cursor/skills/agent-start/SKILL.md` — переименуй префикс skill под проект (`{{project}}-agent-start`)
3. Опционально: skills ролей (`{{project}}-developer`, `{{project}}-team-lead`, …) — по мере роста
4. `.cursor/rules/clear-writing.mdc`, `token-hygiene.mdc`
5. Корневой `AGENTS.md` — из `start-project/AGENTS.md` с подстановкой плейсхолдеров

---

## Шаг 4 — Минимальная документация продукта

Агент **не выдумывает** фичи — фиксирует AS-IS:

| Файл | Минимум |
|------|---------|
| `overview/README.md` | Ссылки на product, architecture, code-map |
| `overview/product.md` | Кто пользователь, 3–5 модулей, каналы |
| `overview/architecture.md` | Слои, деплой, auth в двух абзацах |
| `overview/code-map.md` | Таблица: домен → backend → frontend → … |
| `PROJECT.md` | Быстрый старт, ссылки, команда |

---

## Шаг 5 — Первый спринт

В `workers/sprint/CURRENT.md`:

- **Фокус:** «Bootstrap ИИ-команды + черновик overview»
- **Очередь:** scout (code-map) → documentarian (overview) → team-lead (приоритеты)

---

## Шаг 6 — Проверка готовности

- [ ] Папки **нужных** ролей с IDENTITY + WORKLOG (не обязательно 14)
- [ ] AGENTS.md в корне, ссылка из README репо
- [ ] CURRENT.md с очередью
- [ ] CODE_CHANGE_BOARD пустая, с инструкцией
- [ ] Skill agent-start указывает на workers/ и overview/
- [ ] Владелец открыл Team Lead и подтвердил роли

---

## Промпт для агента (копипаст)

```text
Разверни ИИ-команду по start-project/SETUP.md.

Профиль проекта:
- project_name: …
- packages: …

Делай: шаги 1–5, подставь плейсхолдеры, не коммить без @owner.
Не делай: продуктовый код фич, секреты в workers/.
Отчёт: дерево созданных путей + 3 вопроса владельцу (продукт, стек, приоритет спринта).
```
