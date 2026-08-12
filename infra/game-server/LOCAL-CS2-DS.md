# Локальный CS2 Dedicated Server (@owner)

> Зафиксировано: **2026-08-12** · машина владельца (Windows).  
> Этот инстанс — **основной живой CS2 DS** для разработки, recon плагинов и будущего `live_smoke` (пока Bridge/MatchZy не подключены — в GATE по-прежнему Fake CS2).

---

## Корень установки

| Поле | Значение |
|------|----------|
| **CS2_INSTALL_DIR** | `Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive` |
| **Steam / SteamCMD root** | `Z:\cs2_dedicated_server` |
| **Платформа** | Windows (локальная машина @owner) |
| **Назначение** | Live CS2 для STK: MatchZy + CounterStrikeSharp + STK.Bridge → Platform API |

Путь **не** коммитить в `.env` с секретами — только в локальном `.env` (см. `.env.example` → `CS2_INSTALL_DIR`).

---

## Типовые подпути (относительно CS2_INSTALL_DIR)

```text
game\bin\win64\cs2.exe          # запуск dedicated
game\csgo\                      # cfg, addons, demos
game\csgo\addons\counterstrikesharp\plugins\STK.Bridge\   # цель деплоя Bridge
```

Порты по умолчанию (до смены в cfg): game **27015**, GOTV **27020**.  
Порт команд Bridge (Platform → CS2): **27099** (`STK_BRIDGE_COMMAND_PORT` в `.env`).

---

## Связь с репозиторием

| Режим | Когда | Где |
|-------|-------|-----|
| **Fake CS2** | GATE, CI, разработка без игры | `tools/fake-cs2/` |
| **Этот CS2 DS** | recon, live smoke, матчи на машине владельца | этот документ |
| **Ubuntu VPS** | прод / дистанционный турнир | `scripts/deploy-cs2.sh`, `infra/game-server/README.md` |

Контракт событий/команд: [`CONTRACT.md`](./CONTRACT.md).  
Плагин: [`plugins/STK.Bridge/`](./plugins/STK.Bridge/).

---

## Плагины (установлено 2026-08-12)

| Компонент | Версия | Путь |
|-----------|--------|------|
| Metamod:Source | git **1410** | `game\csgo\addons\metamod\` |
| CounterStrikeSharp | **1.0.371** (with-runtime) | `game\csgo\addons\counterstrikesharp\` |
| MatchZy | **0.8.15** | `plugins\MatchZy\` |
| STK.Bridge | local build | `plugins\STK.Bridge\` |

Переустановка: `pwsh scripts/install-local-cs2-plugins.ps1` из репо.

### ⚠ Один шаг вручную: `gameinfo.gi`

Файл был **занят** (сервер запущен) — Metamod **не подхватится**, пока не добавишь строку:

1. **Останови** dedicated (закрой окно сервера).
2. Запусти **`patch-gameinfo-metamod.bat`** в корне CS2 (рядом с `start-dedicated.bat`).

Проверка после рестарта — в консоли сервера:

```text
meta list
```

Ожидание: **одна** строка `CounterStrikeSharp` — это нормально для CS2.  
MatchZy и STK.Bridge — **дочерние** плагины CSS; они видны в логе при старте:

```text
[MatchZy 0.8.15 LOADED]
STK.Bridge loading match_id=...
```

Команда CSS (если включена): `css_plugins list`

### Шум в логе (можно игнорировать)

| Сообщение | Смысл |
|-----------|--------|
| `USRLOCAL path not found` | норма на dedicated без профиля игрока |
| `Steam Universe is invalid` → потом OK | Steam догружается при старте |
| `Could not PreloadLibrary ... Access violation` | предупреждение CSS, плагины всё равно грузятся |
| `No Steam account token` | LAN-only без GSLT — ок для dev |
| `Unknown command mp_do_warmup_period` | cvar убран/переименован в новой CS2 — уберём из cfg |

### STK.Bridge порт 27099

Если в логе `Command listener failed` — в `config.json` должен быть `"CommandListenHost": "127.0.0.1"` (не `0.0.0.0`). Пересобери Bridge или скопируй свежий `config.json`, рестарт сервера.

### STK.Bridge config

`game\csgo\addons\counterstrikesharp\plugins\STK.Bridge\config.json` — выставь `WebhookSecret` как в `.env` → `CS2_WEBHOOK_SECRET`.

---

## Быстрый запуск (Windows)

В корне установки лежит **`start-dedicated.bat`**:

```text
Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive\start-dedicated.bat
```

Двойной клик **`start-dedicated.bat`** — **Casual** (`game_mode 0`): боты **двигаются**.  
**Не используй Competitive** (`game_mode 1`) с ботами — в vanilla CS2 они стоят на месте (баг Valve); `bot_difficulty` не поможет.

| Файл | Режим |
|------|--------|
| `start-dedicated.bat` | Casual + 9 ботов (локальная тренировка) |
| `start-dedicated-competitive.bat` | Competitive, без ботов (путь к MatchZy / 5v5) |

Конфиг: `game\csgo\cfg\server.cfg`.  
Подключение: `connect 127.0.0.1:27015`.

**Без перезапуска** (консоль сервера) — переключить на casual:

```text
game_type 0; game_mode 0; map de_dust2
```

Потом:

```text
exec stk_bots_active.cfg
```

Если снова замерли:

```text
sv_cheats 1
bot_stop 0
mp_warmup_end
mp_restartgame 1
```

Ручной запуск (эквивалент):

```powershell
cd "Z:\cs2_dedicated_server\steamapps\common\Counter-Strike Global Offensive\game\bin\win64"
.\cs2.exe -dedicated -console -usercon +game_type 0 +game_mode 1 +map de_dust2 +sv_lan 1 -port 27015
```

---

## Live-матч на этом DS (пошагово, TZ009)

**Предпочтительно одной командой** (из корня репо):

```powershell
.\scripts\live-cs2-local.ps1
```

Скрипт сам: `.env` → API → матч → game-server → assign → start-live → `config.json` Bridge.  
Потом: `connect 127.0.0.1:27015` → сыграй раунд (соло + боты ок).

Ручной путь (если скрипт не подходит):

1. **Секреты** — один и тот же `CS2_WEBHOOK_SECRET` в `.env`, в Platform (`POST /game-servers`) и в Bridge `config.json`.
2. **Запуск DS** — `start-dedicated-competitive.bat`. В логе: MatchZy + `STK.Bridge … version=0.2.0` + `Registered CSS handlers`.
3. **Проверка Bridge** — браузер/curl: `http://127.0.0.1:27099/health` → `role=stk-bridge`.
4. **Platform** — зарегистрировать сервер (`endpoint_url=http://127.0.0.1:27099`) → `assign-server` на матч.
5. **Синхрон config** — в `config.json` выставить `MatchId` / `ServerId` как в Platform → **рестарт DS**.
6. **Старт** — в админке **Старт на локальном сервере** или `POST /api/v1/matches/{id}/start-live` (не Fake).
7. **Игра** — `connect 127.0.0.1:27015`, конец раунда → `GET /api/v1/matches/{id}` показывает счёт/раунд.

Чеклист приёмки: [`TZ009-OWNER-SMOKE.md`](../../workers/developer/notes/TZ009-OWNER-SMOKE.md).  
Краткий API-путь: [`README.md`](./README.md) § Live локальный DS.

---

## Следующие шаги (оператор)

1. Убедиться, что DS стартует (`start-dedicated.bat` / competitive).
2. Плагины: Metamod → CSS → MatchZy → STK.Bridge **0.2.0+** (`scripts/install-local-cs2-plugins.ps1` или copy DLL).
3. Заполнить / сверить `config.json` Bridge с матчем на Platform.
4. Register + assign + **start-live** (см. блок «Live-матч» выше).
5. Пройти [`TZ009-OWNER-SMOKE.md`](../../workers/developer/notes/TZ009-OWNER-SMOKE.md) → статус `live_cs2_local=done` только @owner.

После успешного smoke обновить [ALPHA-LIVE-TRACKS.md](../../docs/ALPHA-LIVE-TRACKS.md) §1 (не автоматически при одной только установке Steam).

---

## Env (локальный `.env`)

```env
CS2_INSTALL_DIR=Z:/cs2_dedicated_server/steamapps/common/Counter-Strike Global Offensive
STK_BRIDGE_COMMAND_PORT=27099
CS2_GAME_ENDPOINT_URL=http://127.0.0.1:27099
# CS2_WEBHOOK_SECRET=...  # тот же, что в Bridge config и Platform
```

Слэши `/` в `.env` предпочтительны для кросс-инструментов; в PowerShell путь с пробелами — в кавычках.

---

## Не делать

- Не хранить RCON/секреты в этом файле.
- Не считать установку Steam = GATE live (нужен Bridge + ingest + матч).
- Не путать с путём на Ubuntu VPS (`/opt/cs2` в примерах deploy-cs2) — там отдельный инстанс при деплое.
