# TZ003 — Owner smoke (≤ 15 мин)

> Production Slice GATE. Fake OBS достаточен; живой OBS — опционально.  
> Контракт: [docs/OVERLAY-CONTRACT.md](../../../docs/OVERLAY-CONTRACT.md)  
> Bring-up Agent: [apps/director-agent/README.md](../../../apps/director-agent/README.md)

**Failure B (Agent restart):** закрыт в `apps/director-agent` reconciler (A12) — после
рестарта агент снова применяет **desired**, не историю команд. Проверка: шаг 5b.

---

## Подготовка (один раз)

**Быстрый путь:** [`scripts/dev-remote.ps1`](../../../scripts/dev-remote.ps1) из корня (`.env` с remote `MYSQL_*` + `MYSQL_SSL=1`) — API + Vite overlay/dashboard.

Ручной путь:

```powershell
cd infra/platform
docker compose up -d

cd ../../apps/api
# MySQL host publish :3307 (compose defaults)
$env:MYSQL_HOST="127.0.0.1"; $env:MYSQL_PORT="3307"
$env:MYSQL_USER="stk"; $env:MYSQL_PASSWORD="changeme_stk_dev"; $env:MYSQL_DATABASE="stk"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

В других терминалах (по желанию vite, иначе хватит nginx-сборки / API):

```powershell
cd apps/overlay; npm run dev          # :5173
cd apps/dashboard; npm run dev        # :5174
```

---

## Шаги

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `GET http://127.0.0.1:8000/health` | 200 |
| 2 | `POST /api/v1/matches` с `match_id` (напр. `m_smoke`) | 200, есть `id` |
| 3 | Fake score: `POST /api/v1/internal/cs2/events` (HMAC, `round_end`) **или** skip если нет Fake | score на `GET /matches/{id}` |
| 4 | Открыть overlay: `http://127.0.0.1:5173/overlay/m_smoke` | счёт + watermark **STP** |
| 5 | Agent: `.\stk-director-agent.exe --fake-obs --platform http://127.0.0.1:8000 --match m_smoke --token dev_agent_token_change_me` | лог connected |
| 5b | Остановить Agent (Ctrl+C), запустить снова | снова desired; без падения (Failure B) |
| 6 | Dashboard: `http://127.0.0.1:5174/director/m_smoke` → сцена **intro** | `GET .../production` → desired+actual `intro` |
| 7 | Override: имена команд → Применить | overlay version++ / имена на эфире |
| 8 | `.\scripts\verify.ps1` | **VERIFY OK — TZ003** |

### Минимальные curl (без vite)

```powershell
# сцена
curl -X PATCH http://127.0.0.1:8000/api/v1/matches/m_smoke/production -H "Content-Type: application/json" -d "{\"desired_scene\":\"intro\"}"

# override
curl -X POST http://127.0.0.1:8000/api/v1/matches/m_smoke/overlay/override -H "Content-Type: application/json" -d "{\"team_a_name\":\"Alpha\"}"

curl http://127.0.0.1:8000/api/v1/matches/m_smoke/overlay
curl http://127.0.0.1:8000/api/v1/matches/m_smoke/production
```

---

## Блокеры / notes

| Тема | Статус GATE |
|------|-------------|
| Fake OBS | **достаточен** |
| Реальный OBS | optional ([templates/README.md](../../../apps/director-agent/templates/README.md)) |
| Live CS2 VPS | вне TZ003 (`live_smoke=blocked`) |
| WebRTC / People | → TZ004 |

**Критерий:** шаги 1–8 без устных пояснений ≤ 15 мин.
