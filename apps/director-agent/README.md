# apps/director-agent — Director Agent (Go)

Единственный, кто управляет OBS (инвариант A8). Platform → Agent WS → OBS WebSocket v5  
(или `--fake-obs` для CI без OBS Studio).

Desired production — источник истины (A12): при рестарте агент снова применяет **desired**,  
не историю команд.

OBS-сцены и Browser Source: [`templates/`](templates/README.md).

---

## Быстрый подъём (новый разработчик)

Цель: Fake-матч → overlay в браузере → agent `--fake-obs` → смена сцены из dashboard.

### 1. Platform

```powershell
# Remote MySQL: из корня
.\scripts\dev-remote.ps1 -MatchId m_dev -ApiOnly
# или вручную:
cd ../../apps/api
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Проверка: `http://127.0.0.1:8000/health`

### 2. Создать матч

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/matches `
  -H "Content-Type: application/json" `
  -d "{\"match_id\":\"m_dev\",\"game_server_id\":\"srv_fake\",\"webhook_secret\":\"dev_webhook_secret_change_me\"}"
```

Запомни `id` (например `m_dev`).

### 3. Overlay

```powershell
cd apps/overlay
npm install
npm run dev
# URL для OBS / браузера:
# http://127.0.0.1:5173/overlay/m_dev
```

### 4. Agent (Fake OBS)

```powershell
cd apps/director-agent
copy .env.example .env
# STK_MATCH_ID=m_dev
# STK_AGENT_TOKEN=dev_agent_token_change_me   # как в корневом .env Platform

go test ./...
go build -o stk-director-agent.exe ./cmd/agent
.\stk-director-agent.exe --fake-obs --platform http://127.0.0.1:8000 --match m_dev --token dev_agent_token_change_me
```

### 4b. Agent + Fake WebRTC (комментаторы, TZ004 P5)

Отдельный signaling WS (не ломает OBS reconcile). Publisher создаёт **offer** после `peer_joined`.

```powershell
.\stk-director-agent.exe --fake-obs --fake-webrtc `
  --platform http://127.0.0.1:8000 --match m_dev --token dev_agent_token_change_me
```

1. Создай invite `role=commentator` → `token`
2. Overlay: `http://127.0.0.1:5173/watch?token=<invite>` (без `mock=1`)
3. В `<video>` должен появиться testsrc-паттерн (VP8)

Рестарт агента: signaling переподключается с backoff; `/watch` тоже переподключается — снова получает offer.

TURN (опционально): `docker compose --profile webrtc` + `TURN_*` в `.env`. Agent запрашивает `POST .../turn-credentials`. Без coturn — STUN Google.

OBS Virtual Cam → FFmpeg → Pion: см. [`internal/infrastructure/webrtc/README.md`](internal/infrastructure/webrtc/README.md) (не обязательно для GATE).

### 5. Dashboard режиссёра

```powershell
cd apps/dashboard
npm install
npm run dev
# http://127.0.0.1:5174/director/m_dev
```

Нажми сцену **intro** → в логе агента reconcile;  
`GET /api/v1/matches/m_dev/production` → `desired.scene` и `actual.scene` = `intro`.

Рестарт агента с тем же `--match`: снова применит desired (без истории команд).

### 6. Реальный OBS (опционально)

См. [`templates/README.md`](templates/README.md): сцены + Browser Source + Stream Delay.  
Запуск агента **без** `--fake-obs`, с `STK_OBS_PASSWORD`.

---

## Требования

- Go 1.22+
- Platform API с `/ws/agent/{matchId}` (TZ003 P3)
- OBS Studio 30+ с obs-websocket **или** флаг `--fake-obs`

## Сборка

```powershell
cd apps/director-agent
go mod tidy
go test ./...
go build -o stk-director-agent.exe ./cmd/agent
```

## Запуск (кратко)

```powershell
.\stk-director-agent.exe --fake-obs --platform http://127.0.0.1:8000 --match m_YOUR_ID --token dev_agent_token_change_me
```

```powershell
.\stk-director-agent.exe --platform http://127.0.0.1:8000 --match m_YOUR_ID --token $env:STK_AGENT_TOKEN --obs-url ws://127.0.0.1:4455 --obs-password "…"
```

Секреты OBS только в `.env` / flags — не в git, не в `workers/`.

## Env

Скопируй [`.env.example`](.env.example) → `.env` (gitignore).

| Переменная | Назначение | Dev default |
|------------|------------|-------------|
| `STK_PLATFORM_URL` | HTTP base Platform | `http://127.0.0.1:8000` |
| `STK_MATCH_ID` | id матча | — |
| `STK_AGENT_TOKEN` | как на Platform | `dev_agent_token_change_me` |
| `STK_OBS_URL` | OBS WebSocket | `ws://127.0.0.1:4455` |
| `STK_OBS_PASSWORD` | пароль OBS WS | пусто |

Корневой `.env.example` тоже содержит `STK_AGENT_TOKEN`.

## Структура

```text
cmd/agent/                      entrypoint
internal/domain/                Desired/Actual
internal/application/           Reconciler
internal/presentation/platform/ Platform Agent WS client
internal/infrastructure/obs/    FakeOBS + OBS WS v5 client (whitelist scenes only)
internal/infrastructure/webrtc/ Pion publisher + --fake-webrtc IVF pattern
templates/                      OBS scene stub + Stream Delay checklist
```

Контракт signaling: [`docs/WEBRTC-CONTRACT.md`](../../docs/WEBRTC-CONTRACT.md).
