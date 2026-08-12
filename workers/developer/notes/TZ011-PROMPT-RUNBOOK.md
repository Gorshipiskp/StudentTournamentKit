# TZ011 — PROMPT RUNBOOK · OBS WHIP / MediaMTX / WHEP

> ТЗ: [tasks/011_OBS-WHIP.md](../../../tasks/011_OBS-WHIP.md)  
> База: TZ008 done (FFmpeg live неудовлетворителен); Fake P2P + signaling protocol 1; coturn profile  
> **M = 6** · P6 = GATE · 1 чат = 1 промпт  
> Философия: live-канон комментаторов = OBS WHIP → MediaMTX → `/watch` WHEP; CI остаётся Fake без MediaMTX

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/6 | Spike MediaMTX + OBS WHIP + WHEP; ADR draft; compose/env skeleton | **done** | 2026-08-12 |
| 2/6 | CONTRACT protocol 2 + ADR merge; credentials design зафиксирован | **done** | 2026-08-12 |
| 3/6 | API: whip-publish / whep-play (TTL bearer, path, max 2) | **done** | 2026-08-12 |
| 4/6 | `/watch` WHEP client + Fake/mock без регрессии | **done** | 2026-08-12 |
| 5/6 | Docs/scripts/templates; deprecate live-ffmpeg канон; health publisher | **done** | 2026-08-12 |
| 6/6 | verify Fake + TZ011-OWNER-SMOKE + GATE (`live_whip=done`) | **done** (gate_ready; owner smoke open) | 2026-08-12 |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/6 | §0 · §1 · §2 Frozen · §4 · §6 · WEBRTC-CONTRACT (as-is) · TECH-STACK §4.1 · compose webrtc |
| 2/6 | §2 · §4 · ADR-008/022 · черновик ADR из P1 · spike-заметки |
| 3/6 | §3 · §4 API · turn-credentials pattern · invite caps |
| 4/6 | §3 UX · overlay `/watch` · signalingSubscriber (fake only) |
| 5/6 | §3 · §4 docs · alpha/director · ALPHA-LIVE · scripts live-cs2/dev-remote · Agent README |
| 6/6 | §5 Приёмка · F5 F6 F7 |

---

## P1/6 — Spike + infra skeleton

### Делать

- Поднять **MediaMTX** (Docker): локальный smoke `OBS WHIP → path → WHEP` в браузере (статическая page ок)
- Зафиксировать в `workers/developer/notes/TZ011-SPIKE.md`:
  - точные URL (`…/stk/<id>/whip`, `…/whep`)
  - ICE / публичный host заметки
  - **OBS: WHIP + Twitch одновременно** — да/нет/обход на версии @owner
- Skeleton: `infra/mediamtx/mediamtx.yml` + compose profile `whip` (или расширение `webrtc`)
- `.env.example`: `MEDIAMTX_PUBLIC_URL` / API URL (без секретов в git)
- Черновик ADR (заголовок + решение: MediaMTX на Platform supersede ADR-022 для live)

### Не делать

- Полный Platform credentials API (P3)
- Переписывать `/watch` (P4)
- Ломать Fake CI / удалять Pion
- Коммит без @owner
- Production Ready / Twitch delay redesign

### DoD

- [x] Spike воспроизводим по заметке (команды + скрин/лог «видео есть»)
- [x] Compose/profile + yml skeleton в репо
- [x] ADR draft + SPIKE.md с вердиктом WHIP∥Twitch
- [x] Frozen F1/F2/F9 не нарушены смыслом

### Проверки

- Ручной: OBS Start Streaming (WHIP) → WHEP page играет
- `docker compose …` поднимает MediaMTX без падения

### После P

- WORKLOG; CODE_CHANGE_BOARD; трекер P1=done; **стоп — P2 в новом чате**

---

## P2/6 — CONTRACT + ADR

### Делать

- Влить ADR в [docs/DECISIONS.md](../../../docs/DECISIONS.md): live = WHIP/MediaMTX/WHEP; Fake = protocol 1
- Обновить [docs/WEBRTC-CONTRACT.md](../../../docs/WEBRTC-CONTRACT.md):
  - **protocol 2** live (WHEP; Platform выдаёт URL+bearer; медиа через MediaMTX)
  - protocol 1 Fake без изменения семантики
  - Non-goals: аудио; удаление Fake в этой волне
- Коротко: TECH-STACK §4.1 / ARCHITECTURE ссылка на новый ADR (минимальный diff)
- Зафиксировать path `stk/<matchId>` и форму ответа credentials (для P3)

### Не делать

- Реализацию API handlers (P3)
- UI `/watch` (P4)
- Менять Agent encode-код без пометки deprecated (P5)

### DoD

- [x] ADR принят в DECISIONS (номер + supersede ADR-022 live)
- [x] WEBRTC-CONTRACT описывает dual-mode 1/2
- [x] Контракт credentials согласован с Frozen F7 F9

### Проверки

- Ревью глазами: нет противоречия «без SFU» для live без оговорки ADR

### После P

- WORKLOG; P2=done; новый чат P3

---

## P3/6 — API credentials

### Делать

- `POST /api/v1/matches/{id}/whip-publish` — organizer (или роль режиссёрского доступа по существующей auth-модели) → `{ whip_url, bearer, expires_at, path }`
- `POST /api/v1/matches/{id}/whep-play` — invite `commentator.watch` → `{ whep_url, bearer, expires_at }`
- TTL короткий; path = `stk/<matchId>`; bearer совместим с MediaMTX auth (JWT или internal)
- Лимит **≤2** одновременных WHEP на матч (in-memory/DB — минимально)
- Переиспользовать паттерн [turn.py](../../../apps/api/app/presentation/http/routers/turn.py) / caps
- Unit/integration тесты **без** живого OBS (мок TTL/лимит/404 match)

### Не делать

- Полный WHEP client в overlay (P4)
- Открытый WHIP без bearer
- SFU кроме MediaMTX; LiveKit

### DoD

- [x] Оба endpoint работают по контракту protocol 2
- [x] Третий WHEP получает понятную ошибку (429/403)
- [x] Секреты не логируются
- [x] Тесты зелёные

### Проверки

- pytest на auth / TTL / max 2
- Ручной curl против поднятого MediaMTX (если profile up) — опционально

### После P

- WORKLOG; CODE_CHANGE_BOARD; P3=done; новый чат P4

---

## P4/6 — `/watch` WHEP

### Делать

- Live: `/watch` получает whep credentials → WHEP `RTCPeerConnection` (новый модуль рядом с signalingSubscriber)
- Fake/CI: сохранить signaling + `--fake-webrtc` / `?mock=1`
- API или bootstrapping: явный `media.mode = whep | fake | mock` (минимально)
- UX: нет publisher → «Режиссёр ещё не начал эфир (WHIP)» (не вечный waiting_offer от Pion)
- Не ломать overlay snapshot WS (сцены/счёт)

### Не делать

- Переписывать весь WatchPage с нуля
- Трогать judge/dashboard кроме выдачи URL если нужно одной строкой
- Удалять Pion из Agent

### DoD

- [x] Live path: видео через WHEP при активном OBS WHIP
- [x] Fake/mock path без регрессии
- [x] Понятные статусы при отсутствии publisher

### Проверки

- Vitest на парсер/URL helper если есть
- Ручной: mock + (если MTX up) WHEP

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/6 — Docs, scripts, deprecate FFmpeg live

### Делать

- `docs/alpha/director.md`, Agent templates README, ALPHA-LIVE-TRACKS: трек **`live_whip`** (канон); `live_webrtc` = legacy/deprecated
- Скрипты `live-cs2-local.ps1` / `dev-remote.ps1`: **не** стартовать `--live-webrtc` по умолчанию; печать WHIP URL из API
- Agent README: live-ffmpeg / Virtual Cam — deprecated для комментаторов
- Опционально: match health / production — `whip` publisher online через MediaMTX API
- Черновик `TZ011-OWNER-SMOKE.md` (≤30 мин)

### Не делать

- Вырезать код `--live-webrtc` полностью (можно оставить флаг + warning)
- TZ009 / Twitch GATE
- Большой рефактор Agent

### DoD

- [x] Режиссёр проходит матч по докам без FFmpeg
- [x] OWNER-SMOKE черновик готов
- [x] Скрипты не навязывают fake-obs+fake-webrtc молча, если `.env` с OBS (согласовать с текущим live-cs2 поведением)

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/6 — verify + OWNER-SMOKE + GATE

### Делать

- `verify.ps1`: баннер TZ011; Fake path обязателен; MediaMTX **не** обязателен в CI
- Довести OWNER-SMOKE; @owner: OBS WHIP → `/watch` WHEP (задержка/качество ок)
- Статусы: `live_whip=done` в ALPHA-LIVE-TRACKS + ROADMAP note; tasks/011 → done
- CURRENT_TASK / WORKLOG / трекер

### Не делать

- Коммит без @owner
- Требовать Twitch в GATE
- Менять Frozen молча

### DoD

- [x] VERIFY OK (Fake)
- [ ] @owner smoke пройден → `live_whip=done`
- [x] ТЗ §5 Primary закрыт (кроме owner smoke)

### После P

- СТОП; коммиты @owner; TL: Twitch / TZ010 Production Ready

---

## Эскалация

| Ситуация | Кому |
|----------|------|
| ICE с VPS не сходится | devops + @owner (сеть/firewall) |
| OBS не умеет WHIP+Twitch | TL: принять обход в SPIKE как канон |
| Нужен LiveKit вместо MediaMTX | TL (выход за Frozen F1 path) |
| Diff > ~400 строк за один P | self-review subagent отдельным чатом |
