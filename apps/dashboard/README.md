# apps/dashboard — Режиссёр + админ турниров

Svelte + Vite.

| Маршрут | Назначение |
|---------|------------|
| `/director/{matchId}` | Панель режиссёра (эфир) |
| `/admin` | Вход организатора, список турниров |
| `/admin/tournaments/{id}` | Команды |
| `/admin/tournaments/{id}/bracket` | Сетка + **Старт (Fake)** + ссылки судье/комментатору |
| `/admin/tournaments/{id}/branding` | Лого и цвета |

Управляет эфиром **только через Platform API** (сцены, override overlay, статусы).  
OBS напрямую не трогает (A8) — это зона `apps/director-agent/`.

## Admin: как провести турнир

Шаги на экране (полоска сверху): **Турниры → Команды → Сетка и старт → Брендинг**.

1. **Войти** на `/admin` (логин/пароль из `.env`: `STK_ORGANIZER_USERNAME` / `STK_ORGANIZER_PASSWORD`).
2. **Создать черновик** → при необходимости **Опубликовать**. Можно вести несколько турниров параллельно — команды и матчи не пересекаются.
3. **Команды** — минимум 4 имени (уникальны внутри турнира) + игроки.
4. **Сетка** — «Создать сетку» (4 или 8), расставить команды по слотам. Когда пара полная — появляется матч.
5. **Старт (Fake)** у узла с матчем → статус live без CS2 VPS. **Ссылки для команды** — режиссёр, судья, комментатор (копирование).
6. **Брендинг** (по желанию) — лого и цвета для overlay.

Пустые состояния: нет команд / мало команд / незаполненные слоты — подсказки на экране.

## Dev

Platform API на `:8000` (удобно: [`scripts/dev-remote.ps1`](../../scripts/dev-remote.ps1) из корня).

Ссылки из admin (origins в `.env`):

| Переменная | По умолчанию |
|------------|----------------|
| `STK_DASHBOARD_ORIGIN` | `http://127.0.0.1:5174` |
| `STK_JUDGE_ORIGIN` | `http://127.0.0.1:5175` |
| `STK_WATCH_ORIGIN` | `http://127.0.0.1:5173` |

```powershell
cd apps/dashboard
npm install
npm run dev
```

- Режиссёр: `http://127.0.0.1:5174/director/<matchId>`
- Админ: `http://127.0.0.1:5174/admin`

### Fake-старт матча (GATE)

На экране сетки у узла с `match_id`: **«Старт (Fake)»** → `POST /api/v1/matches/{id}/start`  
Статус → `live`, сцена `ingame`, `game_server_id=srv_fake` если пусто. **Без** live CS2 VPS.

**«Ссылки для команды»** → judge + commentator invites + URL режиссёра (копирование одним кликом).

Vite проксирует `/api` на `http://127.0.0.1:8000`.

## Build

```powershell
cd apps/dashboard
npm install
npm run build
```

Артефакт: `dist/`. Для nginx скопируй в `infra/platform/nginx/html/director/` (и при необходимости отдавай `/admin` тем же SPA).

URL через nginx: `http://127.0.0.1:8080/director/<matchId>`

## Что на экране режиссёра

| Блок | Действие |
|------|----------|
| Матч | статус, счёт, раунд (GET match) |
| Агент / OBS | desired/actual, agent_status, obs_status |
| Сцена эфира | кнопки → `PATCH .../production` |
| Override | имена/счёт → `POST .../overlay/override` |

Опрос статуса ~2 с.
