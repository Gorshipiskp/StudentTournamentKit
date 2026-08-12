---
name: agent-start
description: >-
  Universal session startup for AI team agents. Tiered onboarding L0–L2 for
  token hygiene. Use at the start of every agent chat. Rename to
  {{PROJECT_SLUG}}-agent-start when bootstrapping.
---

# Agent start (универсальный)

**Стандарт:** `.cursor/skills/_shared/WORKER-STANDARDS.md`  
**Память команды:** `workers/README.md`

---

## Уровни

| Уровень | Когда | Действия |
|---------|-------|----------|
| **L0** | Промпт 2+, smoke, точечный фикс | CURRENT_TASK · ТЗ § из runbook · skill роли · **не** AGENTS целиком |
| **L1** | Промпт 1/M, новый домен | L0 + product § · code-map § · IDENTITY · WORKLOG 3 дня |
| **L2** | Team Lead, scout, новый агент | L1 + CURRENT § очередь · ROLES · CODE_CHANGE_BOARD если scout |

---

## Первый ответ в чате

1. Подтверди роль и папку `workers/<slug>/`.
2. Одной фразой — что за продукт (своими словами).
3. Уровень онбординга (L0/L1/L2).
4. Если исполнитель — статус строки в очереди sprint.

---

## Не читать без нужды

- `tasks/README.md` целиком (индекс для TL)
- Журнал `CURRENT.md` целиком
- Файлы >300 строк без grep/limit

---

## Связанные skills

Добавь по роли: `{{PROJECT_SLUG}}-developer`, `-team-lead`, `-scout`, `-product-tm`, …
