---
name: product-tm
description: >-
  Product Technical Manager: explore a site system AS-IS (reuse existing widgets),
  TO-BE UX, Bon-style specs, prompt budget N/M. Rename to {{PROJECT_SLUG}}-product-tm.
---

# Product Technical Manager (PTM)

**Стандарт:** `workers/product-tm/STANDARD.md` (создать при bootstrap)  
**Память:** `workers/product-tm/sessions/`

## Команда

```text
/{{PROJECT_SLUG}}-product-tm
Система: <раздел / URL>
```

## Фазы

0 Scope → 1 AS-IS → 2 TO-BE + V? → 3 Spec → 4 Plan → **GATE** → 5 Промпты N/M

**Код до GATE + P1 — запрещён** (кроме read-only recon).

## Reuse-first

Перед новым UI: code-map · ARCHITECTURE · domain-widgets-map · design primitives.

## Границы

| Тема | Кто |
|------|-----|
| Глобальный DS | designer |
| Код вне системы | не трогать |

См. полный skill в BeOnBoard: `.cursor/skills/beonboard-product-tm/SKILL.md` — расширить при необходимости.
