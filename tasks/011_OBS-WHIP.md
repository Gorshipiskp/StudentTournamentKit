# ТЗ 011 — OBS WHIP (комментаторы без FFmpeg)

| Поле | Значение |
|------|----------|
| **Статус** | **gate_ready** — код/verify P1–P6; `live_whip=done` после @owner smoke |
| **Owner** | @owner (приёмка OBS) / @team-lead (постановка) |
| **Исполнитель** | developer (+ @owner spike P1 + smoke P6) |
| **Этап roadmap** | People optional close / качество `/watch` |
| **Предыдущий** | TZ008 Live WebRTC (FFmpeg/VC) **done** — качество неудовлетворительно |
| **Следующий** | TZ010 Production Ready (отдельно) / live Twitch |

**План:** `.cursor/plans/obs_whip_mediamtx_*.plan.md` (канон: MediaMTX на Platform).  
**Ранбук:** [TZ011-PROMPT-RUNBOOK.md](../workers/developer/notes/TZ011-PROMPT-RUNBOOK.md)

---

## 0. Цель (для людей)

Комментатор по `/watch` видит картинку эфира **из OBS напрямую** (WHIP → MediaMTX → WHEP): без Virtual Camera, без FFmpeg, без двойного encode.  
Режиссёр по-прежнему жмёт сцены в пульте; Agent только управляет OBS.  
CI и репетиции без OBS — по-прежнему Fake (`--fake-webrtc` / mock).

---

## 1. Scope

**В scope:**

- MediaMTX в Docker (profile `whip` / расширение `webrtc`) на Platform
- OBS публикует **WHIP** на path `stk/<matchId>`
- Комментатор `/watch` читает **WHEP** (тот же path)
- Platform: выдача короткоживущих WHIP/WHEP URL + bearer (как TURN)
- Лимит ≤2 активных WHEP на матч (на стороне Platform)
- ADR + обновление WEBRTC-CONTRACT (protocol **2** = live WHEP; protocol **1** = Fake P2P)
- Docs режиссёра / ALPHA-LIVE / скрипты: live-канон без `--live-webrtc` / FFmpeg
- Owner smoke → трек `live_whip=done` (замена канона `live_webrtc` для комментаторов)
- `verify.ps1`: Fake path зелёный **без** MediaMTX

**Вне scope:**

- Аудио WebRTC (Voicemeeter / Discord)
- LiveKit Cloud / платный SaaS
- Удаление Fake/Pion в этой волне (только deprecate live-ffmpeg как канон)
- Twitch через WHIP; FFmpeg Stream Delay
- Production Ready (TZ010)
- CS2 / Bridge (TZ009)

**Уже есть (переиспользовать):**

- Invite + `commentator.watch`, TURN/coturn profile, `/watch` UI
- Agent OBS scenes (без media publisher в live-каноне)
- Паттерн ephemeral credentials: `turn-credentials`

---

## 2. Frozen (не менять без TL)

- **F1:** Картинка с **ноутбука режиссёра (OBS)**; MediaMTX на Platform **принимает и раздаёт** (новый ADR; уточняет ADR-008 / supersede ADR-022 **для live**)
- **F2:** Live = **WHIP/WHEP + MediaMTX**; Fake CI = P2P signaling protocol 1 без SFU
- **F3:** Agent — sole OBS authority для **сцен** (A8); видео publish = OBS WHIP, не Agent encode
- **F4:** Audio WebRTC **выкл**
- **F5:** Primary CI GATE = Fake / без обязательного MediaMTX и OBS
- **F6:** WHIP **без** Twitch Stream Delay (delay только на RTMP/Twitch)
- **F7:** Секреты WHIP/WHEP bearer только в `.env` / runtime; не в git/WORKLOG
- **F8:** A1–A12; коммиты только @owner
- **F9:** Path канон `stk/<matchId>`; ≤2 WHEP credentials/сессии на матч

---

## 3. To-be / UX

1. Compose: MediaMTX up (`--profile whip` или эквивалент)
2. Платформа выдаёт режиссёру WHIP URL + bearer (пульт / staff / скрипт)
3. OBS → Settings → Stream → Service **WHIP** → Start Streaming  
   (Twitch — отдельный выход / отдельный чеклист; spike P1 фиксирует совместимость)
4. Agent: только сцены (real OBS), **без** `--live-webrtc`
5. Комментатор: `/watch?token=…` → WHEP → видео
6. Нет publisher → понятный статус «режиссёр ещё не начал WHIP-stream»

---

## 4. Техника

| Слой | Пути / артефакты |
|------|------------------|
| MediaMTX | `infra/mediamtx/`, compose profile |
| Credentials API | `apps/api` рядом с turn-credentials |
| `/watch` WHEP | `apps/overlay/src/lib/` |
| Контракт | `docs/WEBRTC-CONTRACT.md` protocol 2 |
| ADR | `docs/DECISIONS.md` ADR-0xx |
| Agent | deprecate live-ffmpeg в README/флагах канона |
| Docs | `docs/alpha/director.md`, ALPHA-LIVE-TRACKS, templates |
| Smoke | `workers/developer/notes/TZ011-OWNER-SMOKE.md` |
| Verify | `scripts/verify.ps1` (Fake обязателен; whip optional) |

```text
OBS Program ──WHIP──► MediaMTX (VPS) ──WHEP──► /watch
Agent ──obs-websocket──► OBS (scenes only)
Platform API ──bearer URLs──► OBS + /watch
```

---

## 5. Приёмка

### Primary GATE

- [x] Spike P1: OBS WHIP → MediaMTX → WHEP page (локально или VPS)
- [x] API whip-publish / whep-play + auth + TTL + лимит 2
- [x] `/watch` live через WHEP; Fake/mock без регрессии
- [x] Docs + скрипты без FFmpeg live-канона
- [x] `verify.ps1` → VERIFY OK (Fake)
- [ ] @owner smoke → `live_whip=done` в ALPHA-LIVE-TRACKS
- [x] ADR + CONTRACT обновлены

### Secondary

- [x] Health «publisher online» на матче (MediaMTX API) — `components.whip`
- [x] Deprecate заметка на `--live-webrtc` / Virtual Cam path

---

## 6. Риски

| Риск | Митигация |
|------|-----------|
| OBS не тянет WHIP + Twitch разом | Spike P1; док «два выхода» / приоритет |
| ICE/NAT домашний OBS → VPS | `webrtcAdditionalHosts` + coturn в mediamtx.yml |
| Открытый WHIP в интернет | Обязательный bearer; короткий TTL |
| Ломаем Fake CI | Protocol 1 path не трогать без нужды |

---

*ТЗ 011 · StudentTournamentKit*
