# TZ002 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/8**.  
> Ранбук: [TZ002-PROMPT-RUNBOOK.md](TZ002-PROMPT-RUNBOOK.md) · ТЗ: [tasks/002_GAME-SLICE.md](../../../tasks/002_GAME-SLICE.md)

---

## P1/8 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · code-map § · IDENTITY · WORKLOG · INVARIANTS §6 · ARCHITECTURE §11.
База: TZ001 Foundation уже в репо (layers, outbox, compose).

ТЗ: tasks/002_GAME-SLICE.md — §0 · §1 (contract/Fake) · §2 Frozen · §4.
Промпт 1/8 — Контракт CS2↔Platform + Fake Game Server.

Делать:
- docs или infra/game-server/CONTRACT.md: events, commands, snapshot, HMAC, sequence, command_id
- tools/fake-cs2/: emit events, accept pause/resume/forfeit, snapshot, ack
- README запуска fake против local Platform URL

Не делать: Match FSM Platform (P2), Judge UI, live CS2, Bridge C#, коммит без @owner.

DoD: контракт в репо; fake стартует; self-test/smoke; готов POST на /api/v1/internal/cs2/events.

После: WORKLOG; трекер P1=done в TZ002-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/8 из TZ002-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## P2…P8

Тела — в ранбуке. На P2+: онбординг **L0** — только § из карты P, не ТЗ целиком.
