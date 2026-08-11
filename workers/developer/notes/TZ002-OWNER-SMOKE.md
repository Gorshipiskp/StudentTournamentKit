# TZ002 — Owner smoke (primary GATE, ≤15 мин)

> Live VPS smoke = **blocked** until `@owner` даёт SSH/VPS.

## Предусловия

1. MySQL up: `docker compose --env-file .env -f infra/platform/docker-compose.yml up -d mysql` (порт **3307**)
2. Миграции: в `apps/api` → `alembic upgrade head` (head = `0006_demo_files`)
3. API: `uvicorn app.main:app --reload --port 8000` из `apps/api` (venv)

## Шаги

```text
1. POST /api/v1/game-servers  {server_id, endpoint_url=http://127.0.0.1:27099, webhook_secret}
2. POST /api/v1/matches       {match_id, map_name}
3. POST /api/v1/matches/{id}/assign-server  {server_id}
4. Запустить Fake:
   cd tools/fake-cs2
   .venv\Scripts\python.exe -m fake_cs2 run --match-id <id> --server-id <srv> --listen 27099 --platform-url http://127.0.0.1:8000 --secret <same>
5. Сымитировать 2–3 раунда (emit-rounds или CLI) → GET /api/v1/matches/{id} показывает score
6. POST .../judge/review-request → дождаться pause (round_start buy) → POST .../judge/review-resolve {action:continue, expected_version}
7. pwsh scripts/verify.ps1  → VERIFY OK
```

## Verify локально без smoke UI

```powershell
pwsh -File scripts/verify.ps1
```

Ожидание: артефакты + compose + pytest (A–E) + fake self-test → **VERIFY OK**.  
Строка: `live_smoke=blocked (no VPS / @owner SSH)`.

## Live VPS (когда будет доступ)

1. `deploy-cs2` на VPS (не dry-run) — см. `infra/game-server/README.md`
2. Собрать STK.Bridge (`dotnet` на VPS) — checklist в plugin README
3. MatchZy + Bridge → webhook на Platform → pause через API
4. GOTV demo → durable copy
5. В CURRENT: `live_smoke=done`
