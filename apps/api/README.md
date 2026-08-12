# apps/api — Platform backend

FastAPI-сервис StudentTournamentKit: REST, WebSocket, интеграции с game server и Director Agent.

## Локальный запуск

**Remote MySQL (рекомендуется):** из корня репозитория — [`scripts/dev-remote.ps1`](../../scripts/dev-remote.ps1) (API + миграции + Vite). См. [`scripts/README.md`](../../scripts/README.md).

**Только API вручную:**

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
# MYSQL_* и MYSQL_SSL=1 из корневого .env
uvicorn app.main:app --reload --port 8000
```

Проверка: `GET http://127.0.0.1:8000/health` → `{"status":"ok"}` (без БД).  
Readiness: `GET /ready` → 200 при живой MySQL, 503 если БД недоступна.

Миграции (локально к compose MySQL на порту хоста):

```powershell
$env:MYSQL_HOST="127.0.0.1"; $env:MYSQL_PORT="3307"
alembic upgrade head
```

Remote MySQL: `MYSQL_SSL=1` в `.env`; миграции те же — см. `scripts/dev-remote.ps1`.

В Docker entrypoint API сам выполняет `alembic upgrade head` при старте.

Тесты:

```powershell
pytest -q
```

## Слои

Слои по [docs/LAYERS.md](../../docs/LAYERS.md): `presentation` / `application` / `domain` / `infrastructure`.

Foundation probe (создаёт draft + outbox):

```powershell
curl -X POST http://127.0.0.1:8000/internal/foundation/probe -H "X-Request-ID: demo"
```

Целевой runtime: Python 3.12 (Docker). Локально допустим 3.11+.
