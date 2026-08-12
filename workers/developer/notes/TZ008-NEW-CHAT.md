# TZ008 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/5**.  
> Ранбук: [TZ008-PROMPT-RUNBOOK.md](TZ008-PROMPT-RUNBOOK.md) · ТЗ: [tasks/008_LIVE-WEBRTC.md](../../../tasks/008_LIVE-WEBRTC.md)

---

## P1/5 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § роли комментатор · WEBRTC-CONTRACT · ADR-008/021/022 · TZ004 live optional.
База: TZ004 Fake WebRTC GATE; TZ007 gate_ready; live_webrtc=blocked.

ТЗ: tasks/008_LIVE-WEBRTC.md — §0 · §1 · §2 Frozen · §4.
Промпт 1/5 — контракт Live source + spike OBS Virtual Cam (FFmpeg/dshow) + флаги Agent.

Делать:
- docs/WEBRTC-CONTRACT.md § Live source (Virtual Cam → Agent; Fake = CI default)
- webrtc/README: воспроизводимая команда capture Windows
- Таблица флагов Agent (live vs --fake-webrtc); черновик в Agent README
- Spike: подтвердить имя устройства OBS Virtual Camera

Не делать: полный capture-код (P2); SFU; audio; live Twitch; коммит без @owner.

DoD: контракт согласован с Frozen; README capture + флаги названы.

После: WORKLOG; трекер P1=done в TZ008-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/5 из TZ008-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner: `TZ008-OWNER-SMOKE.md` → `live_webrtc=done`.  
Далее: **TZ009 Live CS2 Local** ([TZ009-NEW-CHAT](TZ009-NEW-CHAT.md)). Production Ready → **TZ010**.
