# TZ003 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/7**.  
> Полный ранбук: [TZ003-PROMPT-RUNBOOK.md](TZ003-PROMPT-RUNBOOK.md) · ТЗ: [tasks/003_PRODUCTION-SLICE.md](../../../tasks/003_PRODUCTION-SLICE.md)

---

## P1/7 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (Student Tournament Platform).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · code-map § · IDENTITY · WORKLOG 3 дня · LAYERS § frontend/agent · INVARIANTS §3.3 §7–8 A8.
Skill: bestcs-tournaments-agent-start.

ТЗ: tasks/003_PRODUCTION-SLICE.md — §0 · §1 · §2 Frozen · §4.
Промпт 1/7 — Контракт overlay+production + Platform snapshot/WS.

Делать:
- docs контракт overlay.snapshot + production desired/actual
- Platform: merge → overlay_revision; GET overlay; WS /ws/overlay/{matchId} full snapshot
- Связка с match score из TZ002 (Fake) → version++
- Pytest на version++ / reconnect snapshot

Не делать: Svelte UI polish (P2); Agent/OBS (P3–P4); Dashboard (P5); коммит без @owner.

DoD: контракт в репо; GET overlay; после Fake event version растёт; WS отдаёт full snapshot.

После: WORKLOG; трекер P1=done в TZ003-PROMPT-RUNBOOK.md; остановись — P2 в новом чате.
```

---

## Однострочник владельца (P2…P7)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/7 из TZ003-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
