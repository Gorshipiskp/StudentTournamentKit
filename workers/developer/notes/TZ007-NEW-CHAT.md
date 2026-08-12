# TZ007 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/6**.  
> Ранбук: [TZ007-PROMPT-RUNBOOK.md](TZ007-PROMPT-RUNBOOK.md) · ТЗ: [tasks/007_TOURNAMENT-ALPHA.md](../../../tasks/007_TOURNAMENT-ALPHA.md)

---

## P1/6 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · ROADMAP этап 6 · TZ001–006 owner smokes (ссылки в tasks/).
База: все срезы TZ001–006 GATE на Fake; live_cs2/live_webrtc/live_twitch = blocked.

ТЗ: tasks/007_TOURNAMENT-ALPHA.md — §0 · §1 runbook · §2 Frozen F1 F5 · §4.
Промпт 1/6 — ALPHA-RUNBOOK + чеклист приёмки @owner.

Делать:
- docs/ALPHA-RUNBOOK.md — цель Alpha, роли, порядок дня, ссылки на TZ002–006 smokes
- Чеклист приёмки владельца (Fake E2E: admin → match → director → judge → overlay/health/audit)
- Scope frozen: 4 teams single-elim, Fake primary

Не делать: alpha-dry-run скрипт (P2); operator guides (P3); код фич; коммит без @owner.

DoD: runbook понятен организатору; чеклист приёмки готов.

После: WORKLOG; трекер P1=done в TZ007-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/6 из TZ007-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner: `TZ007-OWNER-SMOKE.md` + post-mortem (`docs/alpha/POST-MORTEM-TEMPLATE.md`).  
Далее: **TZ008 Live WebRTC** (параллельно) → **TZ009 Production Ready**.
