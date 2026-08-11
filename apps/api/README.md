# apps/api — Platform backend

FastAPI-сервис StudentTournamentKit: REST, WebSocket, интеграции с game server и Director Agent.

## Локальный запуск (P1)

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Проверка: `GET http://127.0.0.1:8000/health` → `{"status":"ok"}` (без БД).  
Readiness: `GET /ready` → 200 при живой MySQL, 503 если БД недоступна.

Миграции (локально к compose MySQL на порту хоста):

```powershell
$env:MYSQL_HOST="127.0.0.1"; $env:MYSQL_PORT="3307"
alembic upgrade head
```

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
