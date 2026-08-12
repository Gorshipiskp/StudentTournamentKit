# TZ008 — PROMPT RUNBOOK · Live WebRTC

> ТЗ: [tasks/008_LIVE-WEBRTC.md](../../../tasks/008_LIVE-WEBRTC.md)  
> База: TZ004 Fake WebRTC GATE; TZ007 Alpha `gate_ready`; `live_webrtc=blocked`  
> **M = 5** · P5 = GATE · 1 чат = 1 промпт  
> Философия: закрыть optional People live — реальное видео комментаторам; CI остаётся на Fake

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/5 | Контракт + spike capture (флаги, путь FFmpeg/dshow) | done | 2026-08-12 |
| 2/5 | Agent: Virtual Cam → VP8 → Pion publisher | done | 2026-08-12 |
| 3/5 | Docs + director guide + ALPHA-LIVE-TRACKS | done | 2026-08-12 |
| 4/5 | Tests + verify (Fake без регрессии) | done | 2026-08-12 |
| 5/5 | TZ008-OWNER-SMOKE + GATE (`live_webrtc=done`) | done | 2026-08-12 (@owner live OK; encode quality bump) |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/5 | §0 · §1 · §2 Frozen · §4 · webrtc/README · ADR-021 |
| 2/5 | §3 · §4 capture · publisher.go · cmd/agent |
| 3/5 | §3 UX · WEBRTC-CONTRACT · alpha/director · ALPHA-LIVE-TRACKS |
| 4/5 | §5 Primary (CI) · verify.ps1 |
| 5/5 | §5 Приёмка · F5 F6 |

---

## P1/5 — Контракт + spike

### Делать

- Уточнить в `docs/WEBRTC-CONTRACT.md` § **Live source** (Virtual Cam → Agent; Fake остаётся default CI)
- Spike Windows: имя устройства OBS Virtual Camera + FFmpeg dshow → VP8 (зафиксировать команду в webrtc/README)
- Спроектировать флаги Agent (например live без `--fake-webrtc` + optional `--webrtc-device=…`); записать в Agent README черновик
- Не писать полный capture-код, если spike ломается — `blocked` с причиной в WORKLOG

### Не делать

- Полный publisher rewrite
- SFU / audio
- Live Twitch

### DoD

- [x] Контракт § live согласован с Frozen F1–F6
- [x] README webrtc: воспроизводимая команда capture на Windows @owner
- [x] Флаги названы (таблица в README)

### После P

- WORKLOG; P1=done; новый чат P2

---

## P2/5 — Agent live publisher

### Делать

- Реализовать capture → `TrackLocalStaticSample` (или эквивалент), тот же `Publisher` / signaling
- Режим Fake (`--fake-webrtc`) без регрессии
- Режим live: Virtual Cam; понятные ошибки, если камера/FFmpeg недоступны
- Минимальный diff; переиспользовать publisher.go

### Не делать

- Dashboard → OBS
- Audio tracks
- Менять протокол signaling (version 1)

### DoD

- [x] Локально: Agent live + `/watch` показывает не-заглушку при Virtual Cam (или явный blocked)
- [x] `--fake-webrtc` по-прежнему работает для CI
- [x] go test пакета webrtc зелёный

### После P

- WORKLOG; CODE_CHANGE_BOARD; P2=done; новый чат P3

> P2 note: smoke — Agent `--live-webrtc` стартует capture (device OK); полный `/watch` E2E — owner / P5.

---

## P3/5 — Docs + оператор

### Делать

- `apps/director-agent/README.md` § Live Virtual Cam (шаги)
- `docs/alpha/director.md` — короткий блок «реальное видео комментаторам»
- `docs/ALPHA-LIVE-TRACKS.md` § `live_webrtc` — шаги = TZ008; статус пока blocked до P5
- templates README: Virtual Cam **без** Stream Delay (уже есть — проверить ссылку)
- Ясный язык (без жаргона в памятке режиссёра)

### Не делать

- Новый UI watch
- Видео-туториалы

### DoD

- [x] Режиссёр может пройти шаги по docs без устных пояснений
- [x] Cross-links: WEBRTC-CONTRACT · ALPHA-LIVE-TRACKS · director.md

### После P

- WORKLOG; P3=done; новый чат P4

---

## P4/5 — Tests + verify

### Делать

- Unit/интеграция там, где стабильно без OBS (мок capture / fake path)
- `scripts/verify.ps1`: артефакты TZ008 + go test; **не** требовать OBS на CI
- Обновить `scripts/README` одной строкой при необходимости

### Не делать

- Обязательный live в verify
- Рефактор платформы

### DoD

- [x] `verify.ps1` зелёный на машине без OBS
- [x] Fake WebRTC self-check/тесты не сломаны

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/5 — OWNER-SMOKE + GATE

### Делать

- `workers/developer/notes/TZ008-OWNER-SMOKE.md` (≤25 мин: OBS Virtual Cam → Agent live → `/watch`)
- Пройти smoke с @owner (или оставить чеклист + `gate_ready` если OBS нет)
- Отметить ТЗ §5; `live_webrtc=done` в ALPHA-LIVE-TRACKS + ROADMAP этап 3 optional
- Закрыть optional checkbox в `tasks/004_PEOPLE-SLICE.md`
- Трекер all done; CURRENT; WORKLOG; CODE_CHANGE_BOARD
- Не объявлять TZ009 Production Ready «закрытым»

### Не делать

- Обязательный live Twitch / CS2
- Коммит без @owner

### DoD

- [x] OWNER-SMOKE написан
- [x] GATE closed (`live_webrtc=done`) — @owner 2026-08-12 real OBS+RTC
- [x] verify зелёный

### После P

- Следующая волна: **TZ009 Production Ready**
- Долг: качество WebRTC (частично поднято 1080p/3500k; тюнить по CPU)---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/5 из TZ008-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
