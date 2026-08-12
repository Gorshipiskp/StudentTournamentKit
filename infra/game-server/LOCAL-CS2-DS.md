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

## Следующие шаги (оператор)

1. Убедиться, что DS стартует (`start-dedicated.bat` или команда выше).
2. Установить Metamod → CounterStrikeSharp → MatchZy (без fork) — см. чеклист в [`README.md`](./README.md).
3. Собрать STK.Bridge (`dotnet build`) и скопировать в `game\csgo\addons\counterstrikesharp\plugins\STK.Bridge\`.
4. Заполнить `config.json` Bridge: `PlatformUrl`, `WebhookSecret`, `MatchId`, `ServerId`.
5. Зарегистрировать сервер в Platform: `POST /api/v1/game-servers` + assign match (см. README § Register).
6. Прогнать live-ветку [`TZ002-OWNER-SMOKE.md`](../../workers/developer/notes/TZ002-OWNER-SMOKE.md) § Live CS2.

После успешного smoke обновить статус `live_cs2` в ROADMAP / CURRENT (не автоматически при одной только установке Steam).

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
