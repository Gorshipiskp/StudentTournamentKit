# TZ011 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/6**.  
> Ранбук: [TZ011-PROMPT-RUNBOOK.md](TZ011-PROMPT-RUNBOOK.md) · ТЗ: [tasks/011_OBS-WHIP.md](../../../tasks/011_OBS-WHIP.md)

---

## P1/6 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § broadcast/commentators · WEBRTC-CONTRACT · TECH-STACK §4.1 · compose webrtc/coturn · TZ008 legacy.
База: TZ008 done (FFmpeg/VC live плох); канон to-be = OBS WHIP → MediaMTX (Platform) → WHEP /watch; Fake P2P остаётся для CI.
План: OBS WHIP / MediaMTX (MediaMTX на VPS/compose, не на ноуте).

ТЗ: tasks/011_OBS-WHIP.md — §0 · §1 · §2 Frozen · §4 · §6.
Промпт 1/6 — spike MediaMTX + OBS WHIP + WHEP; ADR draft; compose/env skeleton.

Делать:
- Docker MediaMTX: OBS WHIP → path → WHEP в браузере
- TZ011-SPIKE.md: URL whip/whep, ICE notes, вердикт OBS WHIP∥Twitch на версии @owner
- infra/mediamtx + compose profile whip (или расширение webrtc); .env.example без секретов
- Черновик ADR: MediaMTX на Platform supersede ADR-022 для live

Не делать: credentials API (P3); /watch WHEP UI (P4); удалять Pion/Fake; ломать verify; коммит без @owner.

DoD: воспроизводимый spike + skeleton compose/yml + ADR draft + SPIKE.md.

После: WORKLOG; CODE_CHANGE_BOARD; трекер P1=done в TZ011-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/6 из TZ011-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner: `TZ011-OWNER-SMOKE.md` → `live_whip=done`.  
FFmpeg/`--live-webrtc` — legacy.  
Далее по TL: **live Twitch** или **TZ010 Production Ready**.
