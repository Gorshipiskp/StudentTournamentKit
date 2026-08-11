# Рабочее пространство ИИ-команды

> **Для кого:** все агенты. **Владелец процесса:** Team Lead (или владелец в маленьком проекте).  
> **Язык:** русский в workers/; код — по правилам репо.

Набор процессов **расчитан на сложную инженерную разработку**. Папки всех 14 ролей, scout, tech-overview и оркестратор — **опциональны**; см. [../SETUP.md](../SETUP.md) § «Масштаб команды».

---

## 1. Зачем эта папка

`workers/` — **единая память команды** вне чатов Cursor.

| Файл | Назначение |
|------|------------|
| `IDENTITY.md` | Кто я, границы, антипаттерны |
| `WORKLOG.md` | Журнал сессий (~3 дня; старше → `worklog_archives/`) |
| `CURRENT_TASK.md` | Активная задача (опционально) |
| `notes/` | Черновики, runbook, smoke |

Общее:

| Файл | Назначение |
|------|------------|
| [ROLES.md](ROLES.md) | Матрица ролей и эскалация |
| [TOKEN-HYGIENE.md](TOKEN-HYGIENE.md) | Экономия токенов |
| [IDEAS.md](IDEAS.md) | Идеи без ТЗ |
| [CODE_CHANGE_BOARD.md](CODE_CHANGE_BOARD.md) | Сигнал scout после кода |
| [sprint/CURRENT.md](sprint/CURRENT.md) | Спринт + очередь |
| [sprint/ORCHESTRATOR.md](sprint/ORCHESTRATOR.md) | Как владельцу открывать вкладки |

---

## 2. Структура папок ролей

```text
workers/
  team-lead/
  developer/
  cybersecurity/
  optimizer/
  devops/
  documentarian/
  tester/
  sales/
  smm/
  scout/
  code-reviewer/
  outcome-ux/
  designer/
  product-tm/
  _templates/
  roles/          ← шаблоны IDENTITY при bootstrap
  sprint/
```

Новая роль — только через обновление `ROLES.md` и этого README.

---

## 3. Первый запуск агента

1. `.cursor/skills/_shared/WORKER-STANDARDS.md`
2. Skill `{{PROJECT_SLUG}}-agent-start` + skill роли
3. Этот README + ROLES (своя строка)
4. `overview/product.md`, `code-map.md` — по задаче
5. `sprint/CURRENT.md` — § очередь
6. Свой `IDENTITY.md`, `WORKLOG.md`, `CURRENT_TASK.md`

Подтверждение Team Lead: `workers/<slug>/ готов`.

---

## 4. После каждой сессии

- [ ] `WORKLOG.md` — что сделано, блокеры, `@роль`
- [ ] `sprint/CURRENT.md` — журнал 1–3 строки, статус очереди
- [ ] `CURRENT_TASK.md` — обновить или закрыть
- [ ] `CODE_CHANGE_BOARD` — если менялся код
- [ ] WORKLOG старше 3 дней → `worklog_archives/`

---

## 5. CURRENT_TASK (шаблон)

См. [_templates/CURRENT_TASK.md](_templates/CURRENT_TASK.md).

---

## 6. Конфликт приоритетов

1. `sprint/CURRENT.md` (очередь, фокус)
2. Постановка Team Lead в чате
3. `{{TASKS_PATH}}/NNN_*.md`
4. Свежий коммит / код

---

## 7. Идеи без ТЗ

[IDEAS.md](IDEAS.md) → triage @team-lead → `{{TASKS_PATH}}/` или отказ.
