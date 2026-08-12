# ТЗ 009 — Live CS2 Local (локальный DS + Bridge → Platform)

| Поле | Значение |
|------|----------|
| **Статус** | **gate_ready** (P1–P5 done; live DS smoke ждёт @owner) |
| **Owner** | @owner (приёмка DS) / @team-lead (постановка) |
| **Исполнитель** | developer (+ @owner на live smoke) |
| **Этап roadmap** | optional live track `live_cs2_local` / перед Production Ready |
| **Предыдущий** | TZ008 Live WebRTC (`done`) |
| **Следующий** | TZ010 Production Ready (или live Twitch — по решению TL) |

---

## 0. Цель (для людей)

На машине владельца крутится **живой CS2 Dedicated Server**. События матча (счёт, раунды, heartbeat) доходят до Platform через **STK.Bridge**. Организатор стартует матч **не только через Fake**, судья видит живой контур, счёт обновляется без `tools/fake-cs2`.

CI и Alpha Fake-путь **не ломаем**.

---

## 1. Scope

**В scope:**

- Довести `STK.Bridge` от skeleton до рабочих webhooks по [CONTRACT.md](../infra/game-server/CONTRACT.md) (минимум: `heartbeat`, `round_start`/`round_end` или эквивалент фазы, `score_changed` / счёт; pause/command path для судьи — если уже в контракте)
- Операторский путь Windows: [LOCAL-CS2-DS.md](../infra/game-server/LOCAL-CS2-DS.md) + register/assign + config Bridge
- Platform: путь **live** (register game-server → assign → старт/ingest без обязательного `start_match_fake` / `srv_fake`) — минимальный diff
- Документация: ALPHA-LIVE-TRACKS § `live_cs2_local`, game-server README / LOCAL-CS2, памятка organizer при необходимости
- Owner smoke на машине с DS @owner
- `verify.ps1`: Fake CI зелёный **без** обязательного CS2 DS
- Статус `live_cs2_local=done` только после @owner smoke

**Вне scope:**

- Обязательный Ubuntu VPS CS2 / `deploy-cs2` live (остаётся отдельным треком)
- Live Twitch (`live_twitch`) — отдельная волна
- Переписывание MatchZy / fork MatchZy (Frozen)
- Новые плагины «ради фичи»
- Production Ready целиком (TZ010)
- Улучшение качества WebRTC

**Уже есть (переиспользовать):**

- `tools/fake-cs2` + ingest API + тесты TZ002
- CONTRACT protocol_version 1
- LOCAL-CS2-DS: Metamod / CSS / MatchZy / Bridge skeleton на `Z:\…`
- `POST /api/v1/game-servers`, `assign-server`, internal cs2 events
- Judge pause / match health (как на Fake)

---

## 2. Frozen (не менять без TL)

- **F1:** MatchZy **не fork**; Bridge — тонкий слой (ADR-023)
- **F2:** События только через CONTRACT (HMAC, sequence); домен без сырого MatchZy JSON
- **F3:** Primary CI GATE = Fake; live DS = owner track
- **F4:** Секреты webhook только в `.env` / config на диске DS — не в git / workers/
- **F5:** `live_cs2_local=done` только после @owner smoke
- **F6:** Минимальный diff; не ломать Fake start / Alpha dry-run

---

## 3. UX / оператор (кратко)

| Роль | Что должно получиться |
|------|------------------------|
| Организатор | Зарегистрировать локальный сервер, assign матч, старт live (не только «Старт Fake») |
| Игрок/владелец | `connect 127.0.0.1:27015`, матч идёт на DS |
| Судья | Пауза/статус на живом контуре (как минимум не хуже Fake buy-pause, если контракт уже есть) |
| Разработчик | `verify` без CS2 остаётся зелёным |

---

## 4. Техника (ориентиры)

| Тема | Где |
|------|-----|
| Контракт | `infra/game-server/CONTRACT.md` |
| Bridge | `infra/game-server/plugins/STK.Bridge/` |
| Локальный DS | `infra/game-server/LOCAL-CS2-DS.md` |
| Fake | `tools/fake-cs2/` |
| Ingest | `apps/api` → `/api/v1/internal/cs2/events` |
| Live track | `docs/ALPHA-LIVE-TRACKS.md` § `live_cs2_local` |
| Smoke | `workers/developer/notes/TZ009-OWNER-SMOKE.md` (создаётся в волне) |

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] Bridge код шлёт нормализованные события (0.2.0 CSS → CONTRACT) — **live DS подтверждение @owner**
- [x] Матч без Fake-эмулятора: путь `start-live` + assign (код/UI)
- [x] `verify.ps1` зелёный (Fake / без DS) — P5
- [ ] `TZ009-OWNER-SMOKE.md` пройден @owner
- [ ] `live_cs2_local=done` в ALPHA-LIVE-TRACKS + ROADMAP

**Состояние волны:** `gate_ready` (2026-08-12). В сессии P6 CS2 DS не отвечал на `:27099` — полный `done` только после @owner smoke (F5).

### Не обязательно для GATE

- [ ] VPS CS2 / GSLT / публичный интернет
- [ ] Twitch
- [ ] Полный 5v5 турнир-день (достаточно одного матча)

**Долг (не блокер):** GOTV demo durable end-to-end на live DS; polish MatchZy load JSON.

---

## 6. Runbook

- `workers/developer/notes/TZ009-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ009-NEW-CHAT.md`
- Промптов: **M = 6** (P6 = GATE)

---

## 7. Ссылки

- [ALPHA-LIVE-TRACKS.md](../docs/ALPHA-LIVE-TRACKS.md)
- [docs/ROADMAP.md](../docs/ROADMAP.md) этап Game / live
- TZ002 Game Slice (Fake primary)
- ADR / invariants по CS2 — по code-map при P1
