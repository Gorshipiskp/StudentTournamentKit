# STK.Bridge — CounterStrikeSharp plugin (skeleton)

Тонкий слой между **MatchZy** и Platform: нормализованные webhooks, heartbeat, приём whitelist-команд.

Контракт: [`../../CONTRACT.md`](../../CONTRACT.md) · `protocol_version: 1`.

**Статус (TZ002 P6):** скелет исходников в репо. Хуки MatchZy/CSS **не** выдуманы — подключать после recon на машине с CS2DS.

---

## Что уже есть

| Компонент | Файл | Назначение |
|-----------|------|------------|
| Plugin entry | `StkBridgePlugin.cs` | `BasePlugin` Load/Unload |
| Config | `config.json`, `StkBridgeConfig.cs` | Platform URL, secret, match/server id, listen port |
| Webhook + HMAC | `WebhookClient.cs` | `POST …/api/v1/internal/cs2/events` |
| Sequence | `SequenceCounter.cs` | монотонный `sequence` per match |
| Heartbeat | `HeartbeatService.cs` | периодический `heartbeat` |
| Commands | `CommandListener.cs` | stub `POST /v1/commands`, `GET /v1/snapshot`, `/health` |

---

## Recon (актуальные ссылки, best effort)

Проверяй версии на VPS — не копируй вслепую:

| Тема | Ссылка |
|------|--------|
| CounterStrikeSharp docs | https://docs.cssharp.dev/ |
| Hello World plugin | https://docs.cssharp.dev/docs/guides/hello-world-plugin.html |
| CSS GitHub | https://github.com/roflmuffin/CounterStrikeSharp |
| NuGet `CounterStrikeSharp.API` | https://www.nuget.org/packages/CounterStrikeSharp.API |
| MatchZy | https://github.com/shobhit-pathak/MatchZy |

На момент скелета: TECH-STACK ориентир **.NET 8**; upstream CSS в 2026 двигается к **.NET 10** (плагины net8 часто грузятся с `RollForward`). На VPS сверь `dotnet --list-runtimes` и версию CSS в `addons/counterstrikesharp`.

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

## BUILD BLOCKER (эта машина разработчика)

```text
Status: blocked_local_build
Reason: .NET SDK (`dotnet`) не найден в PATH на рабочей станции агента (2026-08-11).
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

## Не в scope этого скелета

- Полные CSS listeners / MatchZy callbacks
- Правки MatchZy
- Overlay / RCON из application layer
