# STK.Bridge — CounterStrikeSharp plugin

Тонкий слой между **MatchZy**/CS2 и Platform: нормализованные webhooks, heartbeat, приём whitelist-команд.

Контракт: [`../../CONTRACT.md`](../../CONTRACT.md) · `protocol_version: 1`.

**Статус (0.3.2):** CSS RoundStart/End + bomb FX; warmup → round 0; **round_end всегда** уходит на Platform (анимации/счёт).
(`bomb_*` → overlay `data.fx`). Heartbeat + commands без изменений формы.

---

## Что уже есть

| Компонент | Файл | Назначение |
|-----------|------|------------|
| Plugin entry | `StkBridgePlugin.cs` | `BasePlugin` Load/Unload + CSS event handlers |
| Live state | `MatchLiveState.cs` | round/score/phase для webhook + snapshot |
| Scores | `GameScoreReader.cs` | `cs_team_manager` → `CTeam.Score` |
| Config | `config.json`, `StkBridgeConfig.cs` | Platform URL, secret, match/server id, listen port |
| Webhook + HMAC | `WebhookClient.cs` | `POST …/api/v1/internal/cs2/events` + warn-логи |
| Sequence | `SequenceCounter.cs` | монотонный `sequence` per match |
| Heartbeat | `HeartbeatService.cs` | периодический `heartbeat` |
| Commands | `CommandListener.cs` | stub `POST /v1/commands`, `GET /v1/snapshot`, `/health` |

---

## Recon / P2 hooks (ссылки, без выдуманных API)

Полная карта: **[TZ009-RECON.md](../../../../workers/developer/notes/TZ009-RECON.md)**.

| Тема | Ссылка |
|------|--------|
| CSS game events | https://docs.cssharp.dev/docs/features/game-events.html |
| CSS event handlers example | https://docs.cssharp.dev/examples/WithGameEventHandlers.html |
| `EventRoundStart` / `EventRoundEnd` | https://docs.cssharp.dev/api/CounterStrikeSharp.API.Core.EventRoundStart.html · [EventRoundEnd](https://docs.cssharp.dev/api/CounterStrikeSharp.API.Core.EventRoundEnd.html) |
| Hello World plugin | https://docs.cssharp.dev/docs/guides/hello-world-plugin.html |
| CSS GitHub / NuGet | https://github.com/roflmuffin/CounterStrikeSharp · https://www.nuget.org/packages/CounterStrikeSharp.API |
| MatchZy HTTP events | https://shobhit-pathak.github.io/MatchZy/events_and_forwards/ |
| MatchZy event catalog | https://shobhit-pathak.github.io/MatchZy/events.html |
| MatchZy Events.cs | https://github.com/shobhit-pathak/MatchZy/blob/main/Events.cs |

**GATE events (минимум):** `heartbeat` + `round_start` + `round_end` — **подключены в 0.2.0** (CSS primary).

**Сборка:** target **net8.0** + NuGet `CounterStrikeSharp.API` **1.0.340** (совместимо с SDK 8). На DS стоит CSS **1.0.371** (runtime net10) — плагин грузится через `RollForward`. NuGet 1.0.371 требует net10 SDK — не поднимаем без решения TL.

**После деплоя:** рестарт dedicated → в логе `Registered CSS handlers: EventRoundStart, EventRoundEnd` и `STK.Bridge loading… version=0.2.0`.

**P2 alt (не использован):** MatchZy `matchzy_remote_log_url` → адаптер в Bridge.

---

## Сборка и publish

```bash
cd infra/game-server/plugins/STK.Bridge
dotnet restore
dotnet build -c Release

# Артефакты → папка плагина на CS2DS:
#   .../game/csgo/addons/counterstrikesharp/plugins/STK.Bridge/
# Скопировать: STK.Bridge.dll, STK.Bridge.deps.json, STK.Bridge.pdb, config.json
```

Имя папки плагина = имя DLL (`STK.Bridge`), как в [CSS Hello World](https://docs.cssharp.dev/docs/guides/hello-world-plugin.html).

`config.json` — рядом с DLL; секреты только на VPS, не коммитить прод-значения.

---

## BUILD (owner Windows DS)

```text
Status: builds OK with .NET SDK 8.0.424 (2026-08-12); plugin 0.2.0 deployed to LOCAL-CS2
Install (full stack): scripts/install-local-cs2-plugins.ps1
Bridge-only: dotnet build -c Release → copy DLL/deps/pdb (сохранить config.json)
```

### Checklist на VPS / build machine владельца

1. Установить [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) (или SDK, совместимый с CSS на сервере).
2. `dotnet --version` → записать в WORKLOG.
3. `cd infra/game-server/plugins/STK.Bridge && dotnet restore && dotnet build -c Release`.
4. Если NuGet `CounterStrikeSharp.API` Version в csproj устарел — `dotnet add package CounterStrikeSharp.API` (актуальная версия с nuget.org).
5. Скопировать output в `addons/counterstrikesharp/plugins/STK.Bridge/`.
6. Открыть firewall / `netsh http add urlacl` при необходимости для `CommandListenPort`.
7. Зарегистрировать сервер в Platform (`POST /api/v1/game-servers` + assign) с `endpoint_url=http://<cs2-host>:<CommandListenPort>`.

Пока blocker: **Fake Game Server** (`tools/fake-cs2/`) остаётся primary для GATE.

---

## Конфиг ↔ CONTRACT

| Поле config | Контракт |
|-------------|----------|
| `PlatformUrl` + `EventsPath` | `POST /api/v1/internal/cs2/events` |
| `WebhookSecret` | HMAC `X-STK-Signature` |
| `MatchId` / `ServerId` | поля event/command |
| `ProtocolVersion` | `X-STK-Protocol-Version` / heartbeat payload |
| `CommandListenPort` | HTTP commands как у Fake |

---

## Не в scope / дальше

- Side-effect Pause/Resume на CS2 → P3
- Live start без Fake → P3
- Fork MatchZy (F1)
- Overlay / RCON из application layer
