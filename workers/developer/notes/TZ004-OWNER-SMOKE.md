# TZ004 — Owner smoke (≤ 20 мин)

> People Slice GATE. **`--fake-webrtc` достаточен**; OBS Virtual Cam — optional.  
> Контракт: [docs/WEBRTC-CONTRACT.md](../../../docs/WEBRTC-CONTRACT.md)  
> Agent: [apps/director-agent/README.md](../../../apps/director-agent/README.md) § Fake WebRTC

**Статус:** `live_webrtc=blocked` (нет обязательного OBS Virtual Cam / NAT prod).  
Primary GATE = Fake match + Fake OBS + Fake WebRTC + invites + judge + `/watch`.

---

## Подготовка

```powershell
# Compose MySQL (+ optional TURN)
cd infra/platform
docker compose --env-file ../../.env.example up -d mysql
# optional: docker compose --env-file ../../.env.example --profile webrtc up -d

cd ../../apps/api
$env:MYSQL_HOST="127.0.0.1"; $env:MYSQL_PORT="3307"
$env:MYSQL_USER="stk"; $env:MYSQL_PASSWORD="changeme_stk_dev"; $env:MYSQL_DATABASE="stk"
$env:MYSQL_SSL=""
$env:STK_SESSION_SECRET="dev_session_secret_change_me"
$env:STK_AGENT_TOKEN="dev_agent_token_change_me"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Другие терминалы:

```powershell
cd apps/overlay; npm run dev     # :5173 — overlay + /watch
cd apps/judge; npm run dev       # :5175 — судья
# Fake CS2 (как TZ002) — опционально для паузы на round buy
```

---

## Шаги

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `GET /health` | 200 |
| 2 | `POST /api/v1/matches` → `m_people` + Fake live (round_end HMAC) | match `live` |
| 3 | Agent: `--fake-obs --fake-webrtc --match m_people --token dev_agent_token_change_me` | connected + signaling |
| 4 | `POST /api/v1/invites` role=`judge` и role=`commentator` | `token` в ответе |
| 5 | Judge: `http://127.0.0.1:5175/?token=<judge>` → **Запрос проверки** | review requested |
| 6 | Fake `round_start` phase=`buy` (или Fake CS2) | tech pause / `review_status=paused` |
| 7 | Judge: **Продолжить** | banner cleared; match continues |
| 8 | Watch: `http://127.0.0.1:5173/watch?token=<commentator>` | video (testsrc) + status strip |
| 8b | Повторить review → на `/watch` баннер техпаузы | sync с overlay |
| 9 | Рестарт Agent (Ctrl+C → снова `--fake-webrtc`) | `/watch` переподключается / снова видит video |
| 10 | `.\scripts\verify.ps1` | **VERIFY OK — TZ004** |

### Invites (curl)

```powershell
curl -s -X POST http://127.0.0.1:8000/api/v1/invites -H "Content-Type: application/json" -d "{\"match_id\":\"m_people\",\"role\":\"judge\"}"
curl -s -X POST http://127.0.0.1:8000/api/v1/invites -H "Content-Type: application/json" -d "{\"match_id\":\"m_people\",\"role\":\"commentator\"}"
# revoke: POST /api/v1/invites/revoke {"invite_id":"..."}
```

### TURN (если profile webrtc)

```powershell
curl -s -X POST http://127.0.0.1:8000/api/v1/matches/m_people/turn-credentials -H "X-STK-Agent-Token: dev_agent_token_change_me"
```

---

## Блокеры / notes

| Тема | Статус GATE |
|------|-------------|
| Fake WebRTC (`--fake-webrtc`) | **достаточен** |
| coturn profile | documented / compose OK |
| OBS Virtual Cam → Pion | optional (`live_webrtc=blocked`) |
| Live CS2 VPS | вне TZ004 |
| Max `/watch` | **2** вкладки (4429) |

**Критерий:** шаги 1–10 без устных пояснений ≤ 20 мин.
