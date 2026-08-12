# TZ009 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/6**.  
> Ранбук: [TZ009-PROMPT-RUNBOOK.md](TZ009-PROMPT-RUNBOOK.md) · ТЗ: [tasks/009_LIVE-CS2-LOCAL.md](../../../tasks/009_LIVE-CS2-LOCAL.md)

---

## P1/6 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § game/match · CONTRACT · Bridge skeleton · LOCAL-CS2-DS · TZ002 Fake path.
База: TZ008 done; live_cs2_local=ready; STK.Bridge = skeleton (heartbeat/commands; MatchZy hooks TODO).

ТЗ: tasks/009_LIVE-CS2-LOCAL.md — §0 · §1 · §2 Frozen · §4.
Промпт 1/6 — recon + карта пробелов Bridge ↔ CONTRACT ↔ Platform.

Делать:
- Сверить CONTRACT / Bridge / ingest: что живо на Fake, чего нет на DS
- Заметка TZ009-RECON.md или Bridge README: хуки CSS/MatchZy для P2 (ссылки, без выдуманных API)
- Чеклист LOCAL-CS2-DS готовности (gameinfo, config, порты)
- Назвать минимальный набор event types для GATE

Не делать: реализацию хуков (P2); VPS; Twitch; ломать Fake; коммит без @owner.

DoD: карта пробелов + минимальные события GATE + recon зафиксированы.

После: WORKLOG; трекер P1=done в TZ009-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/6 из TZ009-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner: `TZ009-OWNER-SMOKE.md` → `live_cs2_local=done` (сейчас **gate_ready**).  
Далее по TL: **live Twitch** или **TZ010 Production Ready**.
