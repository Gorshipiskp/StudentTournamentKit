# MediaMTX (TZ011) — WHIP / WHEP для комментаторов

MediaMTX на **Platform** (Compose profile `whip`): OBS публикует WHIP, `/watch` читает WHEP.

Канон path: `stk/<matchId>`.

**Обновление стенда / когда поднимать profile:** [docs/UPDATE.md](../../docs/UPDATE.md).

| Что | URL (local defaults) |
|-----|----------------------|
| WHIP (OBS) | `http://127.0.0.1:8889/stk/<matchId>/whip` |
| WHEP (браузер) | `http://127.0.0.1:8889/stk/<matchId>/whep` |
| Built-in read UI | `http://127.0.0.1:8889/stk/<matchId>` |
| Control API | `http://127.0.0.1:9997/v3/paths/list` |

## Поднять

Из корня репо:

```powershell
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx
```

Публичный ICE host (VPS / LAN): в `.env` задай `MEDIAMTX_WEBRTC_ADDITIONAL_HOSTS` (IP или DNS).

## Spike

См. [workers/developer/notes/TZ011-SPIKE.md](../../workers/developer/notes/TZ011-SPIKE.md).

Статическая WHEP-страница: [spike/whep.html](spike/whep.html).

## Секреты

Bearer/JWT для publish/read — **не** в этом yml для prod (P3: Platform API). Spike открыт (`auth any`).
