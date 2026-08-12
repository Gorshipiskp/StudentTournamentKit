# TZ009 P1 — Recon: Bridge ↔ CONTRACT ↔ Platform

> Дата: **2026-08-12** · Промпт **1/6** · без реализации хуков (P2)

---

## 1. Карта пробелов

| Слой | Живо на Fake | На живом DS (сейчас) | Пробел |
|------|--------------|----------------------|--------|
| **CONTRACT** `protocol_version=1` | Канон для обоих | Тот же канон | — |
| **HMAC + sequence + event envelope** | Fake `events.py` | Bridge `WebhookClient` | Живой путь есть; триггеры матча нет |
| **`heartbeat`** | Fake CLI / loop | Bridge `HeartbeatService` | Готово к smoke (нужны Platform URL + secret + registered server) |
| **`round_start` / `round_end` / `score_changed`** | Fake emit + ingest | **нет** (TODO в `StkBridgePlugin.Load`) | **P2** — главный пробел GATE |
| **`match_loaded` / `match_completed`** | Fake | нет | Желательно после GATE-минимума |
| **`tech_pause_*` + commands Pause/Resume** | Fake apply + events | HTTP stub ack **без** эффекта на CS2 | P2/P3: side-effect + actual events |
| **Snapshot** | Fake real state | Stub zeros (`loaded=false`) | После счёт/раунд |
| **Ingest Platform** | `POST /api/v1/internal/cs2/events` → FSM | Примет те же типы от Bridge | Нет дырки ingest — дырка **источник событий** |
| **Старт матча** | `start_match_fake` → `srv_fake` | Register + assign есть; **live start без Fake** — нет | **P3** |
| **CI / verify** | Fake primary (F3) | DS не требуется | Не трогать |

### Frozen (согласовано)

| ID | Смысл для P2+ |
|----|----------------|
| F1 | MatchZy **не fork**; Bridge тонкий слой |
| F2 | В domain только CONTRACT-типы; сырой MatchZy JSON **не** в application/domain |
| F3 | CI = Fake; live = owner track |
| F4 | Secrets только `.env` / `config.json` на диске DS |
| F5 | `live_cs2_local=done` только после @owner smoke |
| F6 | Не ломать Fake start / Alpha dry-run |

---

## 2. Минимальный набор event types для GATE

По §5 ТЗ («heartbeat + счёт/раунд») и whitelist CONTRACT §3:

| # | `type` | Обязателен для GATE? | Зачем |
|---|--------|----------------------|--------|
| 1 | `heartbeat` | **да** | Пульс Bridge → `last_heartbeat` / health |
| 2 | `round_end` | **да** (предпочтительно) | Счёт + раунд одним событием (`payload.score`, `round`, `map`) |
| 3 | `round_start` | **желательно** (или вместе с #2) | Фаза buy/live; судья / pause-on-buy |
| — | `score_changed` | альтернатива #2 | Если счёт без полного `round_end` |
| — | `match_loaded` | нет для GATE | Удобно для map/status |
| — | `match_completed` | нет для GATE | Долг / после smoke |
| — | `tech_pause_*` | нет для Primary GATE | В scope ТЗ «если контракт есть» — после счёта |

**Итого GATE-минимум:** `heartbeat` + (`round_end` **или** `score_changed` + видимый раунд/фаза).  
Практическая цель P2: `heartbeat` + `round_start` + `round_end` (как у Fake smoke).

---

## 3. Хуки для P2 (ссылки, без выдуманных API)

Два **документированных** пути. Выбрать в P2 один primary; второй — запасной.

### A. Primary (рекомендация): CSS game events → Bridge → CONTRACT

Нормализация **внутри** Bridge (F2). Не пробрасывать raw MatchZy в Platform.

| Что | Ссылка |
|-----|--------|
| Обзор game events | https://docs.cssharp.dev/docs/features/game-events.html |
| Пример `RegisterEventHandler` / `[GameEventHandler]` | https://docs.cssharp.dev/examples/WithGameEventHandlers.html |
| `EventRoundStart` (`round_start`) | https://docs.cssharp.dev/api/CounterStrikeSharp.API.Core.EventRoundStart.html |
| `EventRoundEnd` (`round_end`) | https://docs.cssharp.dev/api/CounterStrikeSharp.API.Core.EventRoundEnd.html |
| Hello World / структура плагина | https://docs.cssharp.dev/docs/guides/hello-world-plugin.html |

**P2 делать:** в `StkBridgePlugin.Load` зарегистрировать слушатели по доке CSS → собрать `payload` CONTRACT → `_webhooks.EmitAsync(...)`.  
Счёт брать из **игрового состояния** (team scores / controller API из CSS docs на версии установленного CSS **1.0.371**) — сигнатуры свойств читать с nuget/API на машине DS, **не** копировать из этой заметки наугад.

**Не делать в P2:** fork MatchZy; новые `type` вне CONTRACT без TL.

### B. Альтернатива: MatchZy HTTP event log (адаптер, не domain)

MatchZy умеет слать JSON на URL (`matchzy_remote_log_url`) — это **их** схема (`event`: `round_end`, …), не CONTRACT.

| Что | Ссылка |
|-----|--------|
| Events & Forwards (HTTP) | https://shobhit-pathak.github.io/MatchZy/events_and_forwards/ |
| Каталог событий (OpenAPI) | https://shobhit-pathak.github.io/MatchZy/events.html |
| Исходник моделей | https://github.com/shobhit-pathak/MatchZy/blob/main/Events.cs |
| Репозиторий / docs home | https://github.com/shobhit-pathak/MatchZy · https://shobhit-pathak.github.io/MatchZy/ |

Если P2 пойдёт этим путём: локальный приёмник **в Bridge** (или рядом) → map в CONTRACT → тот же `WebhookClient`. Platform **не** должен парсить MatchZy JSON (F2).

### Commands (не блокер Primary GATE)

`CommandListener` уже принимает whitelist CONTRACT; side-effect на DS (**не** изобретать): сверить на P2/P3 актуальные команды MatchZy / CSS (`!pause` / admin) по docs MatchZy + cfg — без raw RCON из application layer (CONTRACT §4).

---

## 4. Чеклист LOCAL-CS2-DS — готово к P2

Источник: [`infra/game-server/LOCAL-CS2-DS.md`](../../../infra/game-server/LOCAL-CS2-DS.md). Проверяет @owner / разработчик на машине с `Z:\…`.

| # | Проверка | Ожидание |
|---|----------|----------|
| 1 | `CS2_INSTALL_DIR` | `Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive` |
| 2 | `gameinfo.gi` + Metamod | Сервер **остановлен** → `patch-gameinfo-metamod.bat`; после старта `meta list` → CounterStrikeSharp |
| 3 | Плагины | Metamod **1410**, CSS **1.0.371**, MatchZy **0.8.15**, STK.Bridge в `addons\counterstrikesharp\plugins\STK.Bridge\` |
| 4 | Лог старта | `[MatchZy … LOADED]`, `STK.Bridge loading match_id=…` |
| 5 | Порт игры | **27015** — `connect 127.0.0.1:27015` |
| 6 | Порт команд Bridge | **27099**, `CommandListenHost=127.0.0.1` (не `0.0.0.0`) |
| 7 | `config.json` Bridge | `PlatformUrl`, `MatchId`, `ServerId`, `WebhookSecret` = `.env` `CS2_WEBHOOK_SECRET` |
| 8 | Platform | `POST /api/v1/game-servers` + `assign-server`; тот же secret |
| 9 | Режим для матча | `start-dedicated-competitive.bat` (MatchZy / 5v5); Casual — только боты |
| 10 | Heartbeat smoke | При поднятых DS + API: ingest / `last_heartbeat` без Fake |

Если п.2–4 не зелёные — P2 `blocked` на окружение @owner, не на код Fake.

### P2 результат (2026-08-12)

- Primary path: CSS `EventRoundStart` / `EventRoundEnd` → Bridge → CONTRACT (без MatchZy fork).
- DLL **0.2.0** скопирован в LOCAL-CS2; live DS в сессии P2 **не** отвечал на `:27099` — нужен рестарт dedicated @owner.
- NuGet API остаётся **1.0.340** / net8 (1.0.371 = net10 SDK).

---

## 5. Что уже «живо» на Fake (не ломать)

- Emit всех CONTRACT types, HMAC, sequence
- Commands + real snapshot + pause/resume/forfeit
- Platform ingest + Match FSM + judge pause path
- `start_match_fake` / Alpha dry-run / `verify.ps1`

---

## 6. Очередь после P1

| P | Фокус |
|---|--------|
| **P2** | CSS (или MatchZy-HTTP→Bridge) → `round_*` / score webhooks |
| **P3** | Live start path без обязательного Fake |
| **P4–P6** | Docs, verify, owner smoke → `live_cs2_local=done` |
