# infra/platform — Deploy платформы

Docker Compose для локальной/dev платформы: **api**, **mysql:8**, **nginx**.  
**coturn** — optional profile `webrtc` (People Slice / TZ004; не нужен для Foundation GATE).

```powershell
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile webrtc up -d
```

TURN env: `TURN_HOST`, `TURN_PORT`, `TURN_SECRET`, `TURN_TTL_SECONDS`, `TURN_REALM` (см. `.env.example`).  
API: `POST /api/v1/matches/{id}/turn-credentials` · signaling: `/ws/signaling/{id}` — [docs/WEBRTC-CONTRACT.md](../../docs/WEBRTC-CONTRACT.md).

## Рабочая MySQL (owner, 2026-08-11)

**Канон для разработки у владельца:** удалённая управляемая MySQL (Timeweb Cloud, хост `*.twc1.net`), не контейнер из Compose.

| | |
|---|---|
| Где | Managed MySQL (облако организатора) |
| Как подключаемся | Корневой `.env`: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` |
| Миграции | `cd apps/api` → `alembic upgrade head` (читает `.env` с хоста) |
| Статус схемы | Alembic head на remote (см. `apps/api/alembic/versions/`) |
| Секреты | Только в `.env` / панели хостинга — **не** в git и не в этом README |

Локальный сервис `mysql` в Compose — запасной вариант для офлайн/CI без облака. Если в `.env` уже указан remote-хост:

- API и Alembic с **хоста** используют remote;
- контейнер `api` в Compose по умолчанию всё ещё смотрит на сервис `mysql` внутри сети — **для remote БД не поднимай `api` из Compose** (см. dev-remote ниже).

Для managed MySQL включи TLS в `.env`: `MYSQL_SSL=1` (опционально `MYSQL_SSL_CA=…`). Код: `apps/api/app/infrastructure/persistence/db.py`.

## Dev с remote MySQL (рекомендуется владельцу)

Один скрипт поднимает API + overlay + dashboard на хосте (без Docker mysql/nginx):

```powershell
# из корня репозитория; .env с remote MYSQL_* + MYSQL_SSL=1
.\scripts\dev-remote.ps1 -MatchId m_dev
```

Подробно: [`scripts/README.md`](../../scripts/README.md) § dev-remote.

Ручной вариант (эквивалент только API):

```powershell
cd apps/api
# MYSQL_* и MYSQL_SSL из корневого .env (export / $env: в сессии)
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Overlay/dashboard отдельно: `npm run dev` в `apps/overlay` (:5173) и `apps/dashboard` (:5174).

Проверка связи:

```powershell
# из apps/api, с загруженным корневым .env
curl http://127.0.0.1:8000/ready
```

## Порты (по умолчанию из `.env.example`)

| Сервис | Внутри сети | Хост |
|--------|-------------|------|
| nginx | 80 | **8080** (`NGINX_HTTP_PORT`) |
| api (uvicorn) | 8000 | **8000** (`API_PUBLISH_PORT`) |
| mysql (локальный compose) | 3306 | **3307** (`MYSQL_PUBLISH_PORT`; 3306 часто занят на хосте) |

## Быстрый старт

### Remote MySQL (владелец)

```powershell
cp .env.example .env
# пропиши MYSQL_HOST / USER / PASSWORD / DATABASE / MYSQL_SSL=1
.\scripts\dev-remote.ps1 -MatchId m_dev
```

Compose **не обязателен**. См. § «Dev с remote MySQL» выше.

### Локальный Compose (офлайн / CI)

```powershell
cp .env.example .env
# MYSQL_PUBLISH_PORT=3307 если 3306 занят на Windows
docker compose --env-file .env -f infra/platform/docker-compose.yml up -d --build
```

Проверки:

```powershell
# через nginx (если поднят)
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/ready
# напрямую api
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Остановка:

```powershell
docker compose --env-file .env -f infra/platform/docker-compose.yml down
```

Валидация файла (без подъёма):

```powershell
docker compose --env-file .env -f infra/platform/docker-compose.yml config
```

## Nginx

- `GET /health` → api `/health` (без БД)
- `GET /ready` → api `/ready` (нужна MySQL)
- `/api/` → api (префикс снимается)
- `/` → static stub (`nginx/html/`), позже — сборки overlay/dashboard

При старте контейнера **api** выполняется `alembic upgrade head` (к той БД, что видит контейнер).

## Секреты

Схема переменных: корневой [`.env.example`](../../.env.example).  
Файл `.env` в git не коммитить (см. `.gitignore`).
