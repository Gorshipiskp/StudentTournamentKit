# infra/platform — Deploy платформы

Docker Compose для локальной/dev платформы: **api**, **mysql:8**, **nginx**.  
`coturn` — закомментированный stub (profile `webrtc`, не для GATE).

## Порты (по умолчанию из `.env.example`)

| Сервис | Внутри сети | Хост |
|--------|-------------|------|
| nginx | 80 | **8080** (`NGINX_HTTP_PORT`) |
| api (uvicorn) | 8000 | **8000** (`API_PUBLISH_PORT`) |
| mysql | 3306 | **3307** (`MYSQL_PUBLISH_PORT`; 3306 часто занят на хосте) |

## Быстрый старт

Из корня репозитория:

```powershell
cp .env.example .env
docker compose --env-file .env -f infra/platform/docker-compose.yml up -d --build
```

Проверки:

```powershell
# через nginx
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

При старте контейнера **api** выполняется `alembic upgrade head`.

## Секреты

Схема переменных: корневой [`.env.example`](../../.env.example).  
Файл `.env` в git не коммитить (см. `.gitignore`).
