---
name: prompt-runbook
description: >-
  Writes TZ prompt runbooks (PROMPT-RUNBOOK + NEW-CHAT) with philosophy
  «minimum prompts → maximum agent autonomy» without sacrificing quality.
  Rename to {{PROJECT_SLUG}}-prompt-runbook when bootstrapping.
---

# Prompt Runbook

Сначала `agent-start` + `WORKER-STANDARDS`.

---

## Философия

**Минимум промптов → максимум автономии — без потери качества.**

| Да | Нет |
|----|-----|
| 5–10 крупных P (XL ≤12) | 30 микропромптов |
| 1 P = вертикальный срез + DoD + тесты | P = «подумай» |
| Self-review отдельным P при diff >400 | SR внутри code-P |
| Frozen из ТЗ — закон | Менять scope молча |

---

## Deliverables

| Файл | Назначение |
|------|------------|
| `workers/developer/notes/TZNNN-PROMPT-RUNBOOK.md` | Трекер + тела P1…PM |
| `workers/developer/notes/TZNNN-NEW-CHAT.md` | Копипаст P1 |

---

## Алгоритм

1. Прочитай ТЗ — P1: §0+frozen+scope; P2+: только § из карты P.
2. Режь **вертикали**, не слои (API отдельно от UI — плохо).
3. Последний P — GATE / owner smoke.
4. В каждом P: Делать · Не делать · DoD · проверки.

---

## Исполнение

- **1 чат = 1 Промпт N/M**
- L0 на P2+
- Обновить WORKLOG + CODE_CHANGE_BOARD
