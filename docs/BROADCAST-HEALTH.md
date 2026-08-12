# Broadcast Health — кратко

> Aggregate для режиссёра: `GET /api/v1/matches/{id}/health`.  
> Enum: **HEALTHY · DEGRADED · OFFLINE · UNKNOWN** ([INVARIANTS.md](INVARIANTS.md) §14).

## Компоненты

| Ключ | Смысл |
|------|--------|
| `platform` | API ответил и матч найден |
| `agent` | Director Agent WS (`connected` / `degraded` / `disconnected`) |
| `obs` | OBS через Agent (`connected` / `disconnected`) |
| `overlay` | revision + возраст snapshot |
| `game_server` | Fake (`srv_fake`) = ok без heartbeat; live — по heartbeat |
| `broadcast` | stub (`unknown` / `idle` / `streaming`) — не тянет overall в UNKNOWN |

## Fake OBS

После connect Agent + `obs_status=connected` → `agent`/`obs` **HEALTHY**, `overall` обычно **HEALTHY** (при Fake game).

Director UI (P5) читает тот же endpoint; auth не требуется (как `/production`).

## Журнал (audit)

`GET /api/v1/matches/{id}/audit` — последние действия матча (сцена, судья, старт, …).  
Чтение публичное для панели режиссёра; записи появляются после действий (см. director «Журнал действий»).
