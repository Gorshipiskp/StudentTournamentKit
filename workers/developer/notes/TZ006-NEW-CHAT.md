# TZ006 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/7**.  
> Ранбук: [TZ006-PROMPT-RUNBOOK.md](TZ006-PROMPT-RUNBOOK.md) · ТЗ: [tasks/006_BROADCAST-SLICE.md](../../../tasks/006_BROADCAST-SLICE.md)

---

## P1/7 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · code-map § · DECISIONS ADR-024 · director-agent/templates README §3.
База: TZ001–005 GATE (overlay, director, tournament settings configured_broadcast_delay_seconds).

ТЗ: tasks/006_BROADCAST-SLICE.md — §0 · §1 delay · §2 Frozen F1 F7 · §4.
Промпт 1/7 — Broadcast contract + OBS Stream Delay checklist на director UI.

Делать:
- docs/BROADCAST-DELAY.md (OBS Stream Delay v1, без FFmpeg/Agent automation)
- apps/dashboard director: блок задержки Twitch — значение из tournament settings + RU checklist
- Ссылка на templates README; не трогать OBS API

Не делать: overlay polish (P2); audit/health (P3+); FFmpeg; коммит без @owner.

DoD: director показывает delay hint турнира + checklist; док в репо.

После: WORKLOG; трекер P1=done в TZ006-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/7 из TZ006-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner smoke: `TZ006-OWNER-SMOKE.md` (на P7).  
Далее: **TZ007 Tournament Alpha**.
