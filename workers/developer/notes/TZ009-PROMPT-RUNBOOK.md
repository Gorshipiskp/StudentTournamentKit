# TZ009 — PROMPT RUNBOOK · Live CS2 Local

> ТЗ: [tasks/009_LIVE-CS2-LOCAL.md](../../../tasks/009_LIVE-CS2-LOCAL.md)  
> База: TZ002 Fake GATE; Bridge skeleton; `live_cs2_local=ready`; LOCAL-CS2-DS на машине @owner  
> **M = 6** · P6 = GATE · 1 чат = 1 промпт  
> Философия: закрыть optional live CS2 на Windows @owner; CI остаётся на Fake

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/6 | Recon + карта пробелов (Bridge ↔ CONTRACT ↔ Platform) | **done** | 2026-08-12 |
| 2/6 | Bridge: события с DS (MatchZy/CSS → webhooks) | **done** | 2026-08-12 |
| 3/6 | Platform: live путь (register/assign/start/ingest) | **done** | 2026-08-12 |
| 4/6 | Docs + ALPHA-LIVE + owner smoke draft | **done** | 2026-08-12 |
| 5/6 | Tests + verify (Fake без регрессии) | **done** | 2026-08-12 |
| 6/6 | TZ009-OWNER-SMOKE + GATE (`live_cs2_local=done`) | **done** (gate_ready) | 2026-08-12 |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/6 | §0 · §1 · §2 Frozen · §4 · CONTRACT · Bridge README · LOCAL-CS2-DS |
| 2/6 | §3 · §4 Bridge · CONTRACT events · CSS/MatchZy docs (recon) |
| 3/6 | §3 · start_match · game_servers · ingest · assign-server |
| 4/6 | §3 UX · ALPHA-LIVE-TRACKS · organizer/LOCAL-CS2 · F5 |
| 5/6 | §5 Primary (CI) · verify.ps1 · Fake tests |
| 6/6 | §5 Приёмка · F3 F5 |

---

## P1/6 — Recon + пробелы

### Делать

- Сверить CONTRACT ↔ Bridge skeleton ↔ Platform ingest: что уже принимается, чего нет на живом DS
- Зафиксировать в Bridge README / короткой заметке `workers/developer/notes/TZ009-RECON.md`: какие хуки CSS/MatchZy будут в P2 (без выдуманных сигнатур — ссылки на docs)
- Проверить LOCAL-CS2-DS: `gameinfo.gi`, config Bridge, порты 27015/27099 — чеклист «готово к P2»
- Явно перечислить минимальный набор event types для GATE

### Не делать

- Полную реализацию хуков MatchZy (P2)
- Менять Fake CI
- VPS deploy
- Коммит без @owner

### DoD

- [x] Карта пробелов согласована с Frozen F1–F6
- [x] Минимальный набор событий для GATE назван
- [x] Recon-заметка / README обновлены

### Проверки

- Локально: прочитать CONTRACT + текущий Bridge Load() TODO

### После P

- WORKLOG; P1=done; новый чат P2

---

## P2/6 — Bridge: события с DS

### Делать

- Подключить слушатели CSS/MatchZy **по recon** → нормализованные webhooks (HMAC + sequence)
- Минимум GATE: `heartbeat` (уже есть) + счёт и/или раунд/фаза
- Понятные логи при ошибке webhook / неверном secret
- Пересобрать/задеплоить плагин в LOCAL-CS2 путь (скрипт install, если есть)

### Не делать

- Fork MatchZy
- Новые типы вне CONTRACT без TL
- Platform live-start UI (P3)
- Twitch / WebRTC

### DoD

- [x] С живого DS (или явный blocked с причиной) Platform получает события Bridge — **код+деплой 0.2.0**; live DS не был up в сессии → @owner рестарт + smoke
- [x] Контракт protocol_version=1 соблюдён
- [x] Skeleton command listener не сломан без нужды

### Проверки

- Ручной: DS up → heartbeat в API / логах Platform
- Unit/integration по возможности без DS (мок), если уместно

### После P

- WORKLOG; CODE_CHANGE_BOARD; P2=done; новый чат P3  
- Если DS недоступен агенту: `blocked` + что проверить @owner

---

## P3/6 — Platform live путь

### Делать

- Минимальный путь: register game-server → assign-server → матч **live** без обязательного Fake-эмулятора
- Если нужен `start_match_live` / флаг «не Fake» — минимальный diff; Fake `start_match_fake` без регрессии
- Связка `match_id` / `server_id` / webhook_secret с Bridge `config.json`
- Судья: pause/command до Bridge, если уже в контракте и дырка есть — закрыть минимально

### Не делать

- Переписывать tournament bracket
- VPS-only логику
- Ломать Alpha Fake dry-run

### DoD

- [x] Документированный API/UI путь «матч на локальном DS»
- [x] Ingest обновляет видимый счёт/фазу матча (путь без Fake start; ingest уже был)
- [x] Fake start по-прежнему работает

### Проверки

- Тесты API на assign + ingest (Fake secret ok)
- Ручной сценарий — в P6

### После P

- WORKLOG; P3=done; новый чат P4

---

## P4/6 — Docs + smoke draft

### Делать

- Обновить `LOCAL-CS2-DS.md` / game-server README: пошаговый live матч
- `ALPHA-LIVE-TRACKS.md` §1 — шаги актуальны статусу `ready`
- Черновик `TZ009-OWNER-SMOKE.md` (≤30 мин): DS → Bridge → Platform → счёт
- При необходимости одна правка `docs/alpha/organizer.md` (live vs Fake старт)

### Не делать

- Код фич (только если блокер docs)
- Production Ready

### DoD

- [x] Owner может пройти трек по документам без чата разработчика
- [x] OWNER-SMOKE черновик готов

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/6 — Tests + verify

### Делать

- Убедиться: Fake ingest / start / alpha-dry-run не красные
- `verify.ps1`: баннер TZ009; **без** обязательного CS2 DS
- Точечные тесты на live-path (моки), если добавлены в P3

### Не делать

- Требовать OBS/Twitch в CI
- Большой рефактор тестов

### DoD

- [x] `.\scripts\verify.ps1` → VERIFY OK (Fake)
- [x] Регрессий TZ002/007 Fake нет

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/6 — OWNER-SMOKE + GATE

### Делать

- Довести `TZ009-OWNER-SMOKE.md` до исполнимого чеклиста
- @owner: live DS + Bridge → счёт на Platform → отметить трек
- Статус `live_cs2_local=done` в ALPHA-LIVE-TRACKS + ROADMAP + tasks/009
- CURRENT / CURRENT_TASK / WORKLOG

### Не делать

- VPS live как обязательный GATE
- Коммит без @owner

### DoD

- [x] OWNER-SMOKE написан (исполнимый чеклист)
- [x] GATE closed (`live_cs2_local=done`) **или** `gate_ready` с явной причиной отсрочки @owner — **gate_ready**: DS `:27099` не up в сессии P6
- [x] verify зелёный (P5)

### После P

- Следующая волна: **live Twitch** или **TZ010 Production Ready** (решение TL)
- СТОП — коммиты @owner

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/6 из TZ009-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
