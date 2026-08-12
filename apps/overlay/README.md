# apps/overlay — эфирный overlay (OBS Browser Source)

Svelte + Vite. Показывает счёт, команды, сцену и **watermark STP** по контракту
[`docs/OVERLAY-CONTRACT.md`](../../docs/OVERLAY-CONTRACT.md).

## Dev

Platform API на `:8000` (удобно: [`scripts/dev-remote.ps1`](../../scripts/dev-remote.ps1) из корня).

```powershell
cd apps/overlay
npm install
npm run dev
```

Открой в браузере / OBS Browser Source:

```text
http://127.0.0.1:5173/overlay/<matchId>
```

Vite проксирует `/ws` и `/api` на `http://127.0.0.1:8000`.

Пример с Fake-матчем после TZ002/P1:

1. Создай матч: `POST /api/v1/matches` → возьми `id`
2. Открой URL выше с этим `id`
3. Пришли `round_end` через Fake → счёт на overlay обновится (полный snapshot)

## Commentator `/watch`

Invite-ссылка комментатора (TZ004 P4). Тот же Vite app, другой маршрут:

```text
http://127.0.0.1:5173/watch?token=<invite_raw>
http://127.0.0.1:5173/watch/<invite_raw>
# Без Agent publisher (mock canvas stream):
http://127.0.0.1:5173/watch?token=<invite_raw>&mock=1
```

1. Redeem invite → Bearer session (`commentator.watch`)
2. Overlay WS — счёт / баннер техпаузы
3. Signaling WS subscriber — ждёт `signaling.offer` от Agent (P5)
4. **Лимит: 2** одновременных `/watch` на матч (Platform close `4429`)

Контракт: [`docs/WEBRTC-CONTRACT.md`](../../docs/WEBRTC-CONTRACT.md).

Без `token` — «Доступ закрыт». Без publisher — текст «Ожидание эфира» (или `mock=1` для проверки UI).

## Сборка

```powershell
cd apps/overlay
npm install
npm run build
npm test
```

Артефакт: `apps/overlay/dist/`.

Для nginx (compose): скопируй содержимое `dist/` в `infra/platform/nginx/html/overlay/`
(или смонтируй volume). URL:

```text
http://127.0.0.1:8080/overlay/<matchId>
```

WS идёт через nginx `/ws/` → API.

Опционально прямой API WS (без proxy):

```text
# .env.local
VITE_WS_BASE=ws://127.0.0.1:8000
```

## OBS Browser Source

| Поле | Значение |
|------|----------|
| URL | `http://127.0.0.1:5173/overlay/<matchId>` (dev) или `http://<platform>:8080/overlay/<matchId>` |
| Width × Height | 1920 × 1080 (или под canvas) |
| FPS | 30 |
| Shutdown source when not visible | выкл. (чтобы WS не рвался) |
| Control audio via OBS | не нужно |

Фон страницы **прозрачный** — под Overlay в OBS кладётся захват игры.

Watermark STP всегда в правом нижнем углу (едва заметный) — выключить нельзя.

## Reconnect

Клиент при обрыве WS переподключается с backoff и снова получает **полный** `overlay.snapshot`
(локальный state не патчится — заменяется целиком).
