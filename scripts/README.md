# scripts/

Скрипты локальной разработки и проверок StudentTournamentKit.

| Скрипт | Назначение |
|--------|------------|
| **`dev-remote.ps1`** | **Dev (remote MySQL):** API + overlay + dashboard одной командой |
| **`dev-remote.sh`** | То же для bash/WSL |
| `verify.ps1` | GATE: pytest, сборки, fake-cs2, go test |
| `verify.sh` | То же для bash |
| `deploy-cs2.sh` | CS2 VPS install — **`--dry-run` по умолчанию** |
| `deploy-cs2.ps1` | Windows-хелпер для deploy-cs2 |

Операторский runbook CS2: [`infra/game-server/README.md`](../infra/game-server/README.md).  
Live SSH-деплой — только @owner.

---

## dev-remote — dev-стек с удалённой БД

**Когда использовать:** рабочая MySQL в облаке (Timeweb `*.twc1.net`), разработка на ноутбуке с OBS/overlay/dashboard.  
**Когда не использовать:** офлайн без облака → локальный Compose MySQL + [`verify.ps1`](verify.ps1) или ручной `docker compose`.

### Что поднимает

| Процесс | Порт | Откуда |
|---------|------|--------|
| Platform API (uvicorn, reload) | `8000` | `apps/api` |
| Overlay (Vite dev) | `5173` | `apps/overlay` |
| Dashboard режиссёра (Vite dev) | `5174` | `apps/dashboard` |

**Не поднимает:** Docker Compose, nginx, mysql-контейнер, Director Agent, OBS.  
Vite проксирует `/api` и `/ws` на `:8000` — nginx для dev не нужен.

Перед API: **`alembic upgrade head`** к remote БД (можно `-SkipMigrate`).

### Требования к `.env` (корень репозитория)

```env
MYSQL_HOST=xxxx.twc1.net
MYSQL_PORT=3306
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...
MYSQL_SSL=1
# MYSQL_SSL_CA=C:/path/to/ca.pem   # если Timeweb требует CA

STK_AGENT_TOKEN=dev_agent_token_change_me
API_PORT=8000
```

| Проверка скрипта | Ошибка |
|------------------|--------|
| `MYSQL_HOST=mysql` | только для Docker Compose |
| `MYSQL_HOST=127.0.0.1` без флага | скрипт для remote; локаль — `-AllowLocalDb` |
| `MYSQL_SSL` выкл. + remote host | предупреждение (Timeweb часто требует TLS) |

Схема переменных: [`.env.example`](../.env.example). Секреты не коммитить.

### Windows (PowerShell)

```powershell
cd C:\BestCSTournaments
.\scripts\dev-remote.ps1 -MatchId m_live
```

Откроются **3 окна** PowerShell (логи отдельно). Остановка: **Ctrl+C** в каждом или закрыть окна.

**Флаги:**

| Флаг | Эффект |
|------|--------|
| `-MatchId m_live` | id матча в подсказках URL и curl |
| `-ApiOnly` | только API, без Vite |
| `-SkipMigrate` | не запускать alembic |
| `-AllowLocalDb` | разрешить `MYSQL_HOST=127.0.0.1` |

**URL после старта:**

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
http://127.0.0.1:5173/overlay/<matchId>
http://127.0.0.1:5174/director/<matchId>
```

**Создать матч (PowerShell):**

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/matches" `
  -ContentType "application/json" `
  -Body '{"match_id":"m_live","game_server_id":"srv_fake","webhook_secret":"dev_webhook_secret_change_me","map_name":"de_mirage"}'
```

**Agent + OBS** — вручную после настройки сцен OBS ([`apps/director-agent/templates/README.md`](../apps/director-agent/templates/README.md)):

```powershell
cd apps/director-agent
.\stk-director-agent.exe --platform http://127.0.0.1:8000 --match m_live `
  --token dev_agent_token_change_me --obs-url ws://127.0.0.1:4455 --obs-password "…"
```

### bash / WSL

```bash
cd /path/to/BestCSTournaments
chmod +x scripts/dev-remote.sh
./scripts/dev-remote.sh m_live
```

Процессы в **фоне одного терминала**; **Ctrl+C** останавливает все.

```bash
API_ONLY=1 ./scripts/dev-remote.sh          # только API
SKIP_MIGRATE=1 ./scripts/dev-remote.sh      # без alembic
ALLOW_LOCAL_DB=1 ./scripts/dev-remote.sh    # localhost MySQL
```

### Связанные документы

- Platform / remote MySQL: [`infra/platform/README.md`](../infra/platform/README.md)
- Owner smoke TZ003: [`workers/developer/notes/TZ003-OWNER-SMOKE.md`](../workers/developer/notes/TZ003-OWNER-SMOKE.md)
- Overlay / OBS Browser Source: [`apps/overlay/README.md`](../apps/overlay/README.md)

### Вспомогательный модуль

[`lib/Import-DotEnv.ps1`](lib/Import-DotEnv.ps1) — загрузка `.env` в процесс (используется `dev-remote.ps1`).

---

## verify — GATE перед merge

```powershell
.\scripts\verify.ps1
```

Локальный pytest по умолчанию смотрит на compose MySQL `:3307` (см. скрипт). Remote БД для verify не обязательна.
