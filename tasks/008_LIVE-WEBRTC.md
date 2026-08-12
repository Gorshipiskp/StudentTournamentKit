# ТЗ 008 — Live WebRTC (реальное видео комментаторам)

| Поле | Значение |
|------|----------|
| **Статус** | **done** (GATE 2026-08-12; @owner: real OBS + live WebRTC OK) |
| **Owner** | @owner (приёмка OBS) / @team-lead (постановка) |
| **Исполнитель** | developer (+ @owner на live smoke) |
| **Этап roadmap** | 3 optional close / перед Production Ready |
| **Предыдущий** | TZ007 Tournament Alpha (`gate_ready`; Fake primary) |
| **Следующий** | TZ009 Live CS2 Local |

---

## 0. Цель (для людей)

Комментатор по invite-ссылке `/watch` видит **реальную картинку эфира** с ноутбука режиссёра (OBS Virtual Camera → Agent → браузер), а не тестовую заглушку. Fake WebRTC остаётся для CI и репетиций без OBS.

---

## 1. Scope

**В scope:**

- Director Agent: захват **OBS Virtual Camera** → encode VP8 → существующий Pion publisher / signaling (тот же контракт, что Fake)
- Флаги/конфиг: live-источник vs `--fake-webrtc` (CI по умолчанию Fake)
- Документация: `WEBRTC-CONTRACT` § live, Agent README, `docs/alpha/director.md`, `ALPHA-LIVE-TRACKS` трек `live_webrtc`
- Owner smoke на машине с OBS Virtual Cam
- `verify.ps1`: артефакты TZ008; CI **без** обязательного OBS (Fake path зелёный)
- Статус `live_webrtc=done` только после @owner smoke

**Вне scope:**

- Аудио WebRTC (F7 / ADR — Voicemeeter вне STK)
- SFU / LiveKit / mediasoup
- FFmpeg **Stream Delay** buffer (ADR-024 v2) — delay только OBS для Twitch
- Live Twitch / live CS2 (отдельные треки)
- Переписывание `/watch` UI с нуля (только если блокер)
- TZ009 Production Ready целиком

**Уже есть (переиспользовать):**

- Signaling + TURN + invites (TZ004)
- `--fake-webrtc` + `TrackLocalStaticSample` publisher
- `/watch` + mock; ADR-008 / ADR-021 / ADR-022
- Черновик пути: `apps/director-agent/internal/infrastructure/webrtc/README.md`

---

## 2. Frozen (не менять без TL)

- **F1:** Видео с **ноутбука режиссёра** (Agent), не media-relay на Platform VPS (ADR-008)
- **F2:** P2P + TURN, без SFU; ≤2 subscriber (ADR-022 / контракт)
- **F3:** Agent — sole OBS authority (A8); dashboard не говорит с OBS
- **F4:** Audio WebRTC **выкл** в v1
- **F5:** Primary CI GATE = Fake publisher; live Virtual Cam = owner track
- **F6:** Virtual Cam / WebRTC **без** Twitch Stream Delay (ADR-009 / ADR-024)
- **F7:** Секреты в `.env`; коммиты только @owner
- **F8:** A1–A12

---

## 3. To-be / UX

1. Режиссёр: OBS → сцены + **Start Virtual Camera** (превью без Stream Delay)
2. Agent: live WebRTC (не `--fake-webrtc`) + при необходимости Fake OBS или реальный OBS
3. Организатор: invite комментатора
4. Комментатор: `/watch?token=…` → **реальное** видео эфира + статус/техпауза
5. Рестарт Agent → переподключение (как Fake path)

---

## 4. Техника

| Слой | Пути |
|------|------|
| Capture → Pion | `apps/director-agent/internal/infrastructure/webrtc/` |
| Flags / main | `apps/director-agent/cmd/agent/` |
| Контракт | `docs/WEBRTC-CONTRACT.md` |
| Live track | `docs/ALPHA-LIVE-TRACKS.md` § `live_webrtc` |
| Памятка | `docs/alpha/director.md` |
| Smoke | `workers/developer/notes/TZ008-OWNER-SMOKE.md` |
| Verify | `scripts/verify.ps1` |

Предпочтительный capture (ADR-021): FFmpeg dshow `OBS Virtual Camera` → VP8/IVF или raw frames → существующий track. Альтернатива — только если spike P1 докажет блокер.

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] Live capture path в Agent (Virtual Cam → publisher); Fake path без регрессии
- [x] Документация + флаги понятны режиссёру
- [x] `verify.ps1` зелёный (Fake / без OBS) — **VERIFY OK — TZ008**
- [x] @owner прошёл live: реальный OBS + `--live-webrtc` → `/watch` (2026-08-12)
- [x] `live_webrtc=done` в ALPHA-LIVE-TRACKS + ROADMAP People optional
- [x] TZ004 optional checkbox закрыт

**Долг (не блокер GATE):** качество encode (bitrate/scale) — поднято после приёмки; дальнейший тюнинг при необходимости.

### Не обязательно для GATE

- [ ] NAT/prod TURN stress за пределами локальной сети
- [ ] Два комментатора одновременно на live (желательно в smoke)

---

## 6. Runbook

- `workers/developer/notes/TZ008-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ008-NEW-CHAT.md`
- Промптов: **M = 5** (P5 = GATE)

---

## 7. Паритет

Один publisher (Agent). Браузер комментатора — тот же `/watch`, что на Fake.
