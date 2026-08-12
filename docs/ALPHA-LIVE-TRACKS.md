# Alpha — optional live tracks

> **Не часть Primary GATE.** Alpha принимается на Fake ([ALPHA-RUNBOOK.md](ALPHA-RUNBOOK.md)).  
> День матча / 2-й турнир (Fake primary): [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md).  
> Live-треки — по готовности @owner.  
> ТЗ: [tasks/007_TOURNAMENT-ALPHA.md](../tasks/007_TOURNAMENT-ALPHA.md) §5 optional.

Изменить статус на `done` может только @owner после прохождения трека (дата + заметка ниже).  
**blocked** = нельзя пробовать (нет инфры / не открыто). **ready** = можно проходить сегодня.

---

## Пробный матч — что делать тебе

Порядок на **один** живой пробный день (после того как Platform / dashboard / overlay / judge уже подняты):

### Уже закрыто

1. **OBS + комментаторы (legacy VC)** — `live_obs` + `live_webrtc` = **done** (TZ008).  
   **Новый канон комментаторов:** трек **`live_whip`** (OBS WHIP → MediaMTX → `/watch` WHEP) — см. §5 / TZ011.

### Открыто сейчас (снять руками)

2. **CS2 локально** (`live_cs2_local` = **ready** / gate_ready)
   - **Один скрипт:** `.\scripts\live-cs2-local.ps1` → `connect 127.0.0.1:27015` → раунд
   - Документ: [`LOCAL-CS2-DS.md`](../infra/game-server/LOCAL-CS2-DS.md) · smoke: [TZ009-OWNER-SMOKE.md](../workers/developer/notes/TZ009-OWNER-SMOKE.md)

3. **Комментаторы WHIP** (`live_whip` = **ready**)
   - MediaMTX profile `whip` · OBS Service **WHIP** · `/watch` (default WHEP)
   - Smoke: [TZ011-OWNER-SMOKE.md](../workers/developer/notes/TZ011-OWNER-SMOKE.md)

4. **Twitch** (`live_twitch` = **ready**)
   - OBS → Дополнительно → **Stream Delay ~90–120 с** ([templates §3](../apps/director-agent/templates/README.md))
   - Stream key Twitch → старт трансляции (**отдельный выход** от WHIP)
   - На панели режиссёра пройди чек-лист «Задержка Twitch»
   - Контракт: [BROADCAST-DELAY.md](BROADCAST-DELAY.md)

5. После прохода — здесь статус → `done` + дата; кратко в [post-mortem](alpha/POST-MORTEM-TEMPLATE.md).

### Параллельно (не блокер live)

- Fake Alpha smoke / post-mortem: [TZ007-OWNER-SMOKE.md](../workers/developer/notes/TZ007-OWNER-SMOKE.md) — закрывает TZ007 GATE на бумаге.

---

## Сводка

| Трек | Ключ | Статус | Кратко |
|------|------|--------|--------|
| Локальный CS2 DS + Bridge → Platform | `live_cs2_local` | **ready** | MatchZy + STK.Bridge на машине владельца |
| Реальный OBS (не Fake) | `live_obs` | **done** | Agent без `--fake-obs` (@owner 2026-08-12 с TZ008) |
| Twitch + Stream Delay | `live_twitch` | **ready** | OBS Stream Delay ~90–120 с (не FFmpeg) |
| **OBS WHIP → MediaMTX → `/watch`** | `live_whip` | **ready** · gate_ready | Канон комментаторов (TZ011); ждёт @owner smoke |
| WebRTC Virtual Cam (legacy) | `live_webrtc` | **done** · **deprecated** | TZ008; заменён каноном `live_whip` |

---

## 1. `live_cs2_local` — локальный CS2 Dedicated Server

**Цель:** игровой сервер на Windows @owner шлёт события в Platform (webhook Bridge), матч не только Fake-старт.

**Статус:** **ready** → волна TZ009 **gate_ready** (2026-08-12).  
Код/доки/verify готовы; `live_cs2_local=done` — после [TZ009-OWNER-SMOKE](../workers/developer/notes/TZ009-OWNER-SMOKE.md) @owner (F5).  
ТЗ: [009_LIVE-CS2-LOCAL.md](../tasks/009_LIVE-CS2-LOCAL.md)

**Шаги (обзор):**

1. Установка и плагины: [`LOCAL-CS2-DS.md`](../infra/game-server/LOCAL-CS2-DS.md) (+ § Live-матч)
2. `CS2_INSTALL_DIR` + секреты webhook в `.env` (не в git)
3. Запуск DS (`start-dedicated-competitive.bat`) → Bridge `:27099/health`
4. Platform: `POST /game-servers` → `assign-server` → **`start-live`** / кнопка «Старт на локальном сервере»
5. Сверь Bridge `config.json` (`MatchId` / `ServerId` / secret) → рестарт DS при смене
6. Раунд в CS2 → `GET /matches/{id}` показывает счёт; судья pause на endpoint Bridge

**Owner smoke (канон):** [TZ009-OWNER-SMOKE.md](../workers/developer/notes/TZ009-OWNER-SMOKE.md)  
**Операторский README:** [`infra/game-server/README.md`](../infra/game-server/README.md) § Live локальный DS  
**Устарело как primary:** TZ002 § Live CS2 — используй TZ009-OWNER-SMOKE

**Не делать в Alpha:** новые плагины; обязательный VPS CS2 для GATE.

| Поле | Значение |
|------|----------|
| Пройдено @owner | |
| Дата | |
| Заметка | |

---

## 2. `live_obs` — реальный OBS

**Цель:** Agent управляет живым OBS Studio (WebSocket v5), не `--fake-obs`.

**Статус:** **done** (2026-08-12 @owner: вместе с live WebRTC, без `--fake-obs`)

**Шаги (обзор):**

1. Шесть сцен + Browser Source overlay: [`apps/director-agent/templates/README.md`](../apps/director-agent/templates/README.md) §1
2. Включить obs-websocket, пароль → `STK_OBS_PASSWORD` / флаг Agent ([`apps/director-agent/README.md`](../apps/director-agent/README.md) § «Реальный OBS»)
3. Agent **без** `--fake-obs` для матча
4. С панели `/director/{матч}` сменить сцену → в OBS переключается одноимённая
5. Health: agent + OBS «в порядке»

**Fake-путь (GATE):** `--fake-obs` · [docs/alpha/director.md](alpha/director.md)

| Поле | Значение |
|------|----------|
| Пройдено @owner | да |
| Дата | 2026-08-12 |
| Заметка | Real OBS + scene control в сессии TZ008 / live RTC |

---

## 3. `live_twitch` — Twitch + Stream Delay

**Цель:** публичный эфир на Twitch с задержкой OBS; комментаторы смотрят без этой задержки (WebRTC/превью).

**Статус:** **ready** (2026-08-12 — блокер снят; нужен stream key + Stream Delay в OBS)

**Шаги (обзор):**

1. Контракт: [`docs/BROADCAST-DELAY.md`](BROADCAST-DELAY.md) (ADR-024 v1)
2. Чек-лист OBS Stream Delay: [templates/README.md §3](../apps/director-agent/templates/README.md) · блок на панели режиссёра
3. Stream key Twitch в OBS → Трансляция
4. Значение ~90–120 с (или hint турнира `configured_broadcast_delay_seconds`)
5. Пробный выход / запись — убедиться, что delay включён

**Важно:** Agent **не** выставляет delay автоматически. **Не** использовать FFmpeg delay-buffer в v1 (это fallback v2).

**Smoke-наследник:** [TZ006-OWNER-SMOKE.md](../workers/developer/notes/TZ006-OWNER-SMOKE.md)

| Поле | Значение |
|------|----------|
| Пройдено @owner | |
| Дата | |
| Заметка | |

---

## 4. `live_webrtc` — Virtual Cam (legacy / deprecated)

**Цель (историческая):** картинка эфира в `/watch` с OBS Virtual Cam + FFmpeg + Pion.

**Статус:** **done** (2026-08-12) · **deprecated как канон** — см. **`live_whip`** (§5) и [ADR-037](DECISIONS.md).  
ТЗ: [008_LIVE-WEBRTC.md](../tasks/008_LIVE-WEBRTC.md). Флаг Agent `--live-webrtc` оставлен, но **не** использовать в матч-день.

| Поле | Значение |
|------|----------|
| Пройдено @owner | да |
| Дата | 2026-08-12 |
| Заметка | Real OBS + live WebRTC OK; superseded by live_whip |

---

## 5. `live_whip` — OBS WHIP → MediaMTX → `/watch` WHEP

**Цель:** комментатор видит Program OBS **без** Virtual Camera и **без** FFmpeg encode в Agent.

**Статус:** **ready** → волна TZ011 **gate_ready** (2026-08-12).  
Код/доки/verify готовы; `live_whip=done` — после [TZ011-OWNER-SMOKE](../workers/developer/notes/TZ011-OWNER-SMOKE.md) @owner.  
ТЗ: [011_OBS-WHIP.md](../tasks/011_OBS-WHIP.md) · контракт: [WEBRTC-CONTRACT.md](WEBRTC-CONTRACT.md) protocol 2 · ADR-037

**Шаги:**

1. `docker compose --profile whip up -d mediamtx` (+ `MEDIAMTX_*` в `.env`)
2. Agent: **только сцены** (реальный OBS, **без** `--live-webrtc`)
3. Organizer: `POST …/whip-publish` → OBS Service **WHIP** + bearer → Start Streaming
4. Комментатор: `/watch?token=…` (default WHEP; Fake rehearsal: `?media=fake`)
5. Twitch — **отдельный** выход OBS (Stream Delay только на Twitch)

| Поле | Значение |
|------|----------|
| Пройдено @owner | |
| Дата | |
| Заметка | |

---

## Как отмечать

После прохождения трека @owner:

1. Статус в таблице сверху → `done`
2. Заполнить «Пройдено / Дата / Заметка» в § трека
3. Упомянуть в post-mortem ([POST-MORTEM-TEMPLATE.md](alpha/POST-MORTEM-TEMPLATE.md))

Primary Fake GATE при этом **не** переоткрывается.
