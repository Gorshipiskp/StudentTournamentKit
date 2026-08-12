---
name: bestcs-tournaments-agent-start
description: >-
  Session startup for BestCS Tournaments AI team agents. Tiered onboarding
  L0–L2 for token hygiene. Use at the start of every agent chat.
---

# Agent start — BestCS Tournaments

**Стандарт:** `.cursor/skills/_shared/WORKER-STANDARDS.md`  
**Память команды:** `workers/README.md`

---

## Уровни

| Уровень | Когда | Действия |
|---------|-------|----------|
| **L0** | Промпт 2+, smoke, точечный фикс | CURRENT_TASK · ТЗ § из runbook · skill роли · **не** AGENTS целиком |
| **L1** | Промпт 1/M, новый домен | L0 + product § · code-map § · IDENTITY · WORKLOG 3 дня |
| **L2** | Team Lead, новый агент | L1 + CURRENT § очередь · ROLES · TECH-LEAD-BRIEF § по задаче |

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
- `docs/TECH-LEAD-BRIEF.md` целиком (900+ строк) — только § по задаче
- Файлы >300 строк без grep/limit

---

## Связанные skills

Добавь по роли: `bestcs-tournaments-developer`, `-team-lead`, … (по мере роста)
