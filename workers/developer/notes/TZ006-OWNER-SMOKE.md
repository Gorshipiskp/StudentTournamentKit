# TZ006 — Owner smoke (≤ 25 мин)

> Broadcast Slice GATE. **Fake OBS + Fake match** — без live Twitch и без live CS2.  
> Контракты: [BROADCAST-DELAY.md](../../../docs/BROADCAST-DELAY.md) · [BROADCAST-HEALTH.md](../../../docs/BROADCAST-HEALTH.md)  
> Ранбук: [TZ006-PROMPT-RUNBOOK.md](TZ006-PROMPT-RUNBOOK.md)

**Статус:** Primary GATE = delay checklist + 6 overlay scenes + health panel + audit UI на Fake OBS.  
Наследует: `live_cs2=blocked`, `live_webrtc=blocked`. **`live_twitch=blocked`** (реальный Twitch — optional).

---

## Подготовка

```powershell
# Compose MySQL (+ API уже с миграциями)
cd infra/platform
docker compose --env-file ../../.env.example up -d mysql

cd ../../apps/api
$env:MYSQL_HOST="127.0.0.1"; $env:MYSQL_PORT="3307"
$env:MYSQL_USER="stk"; $env:MYSQL_PASSWORD="changeme_stk_dev"; $env:MYSQL_DATABASE="stk"
$env:MYSQL_SSL=""
$env:STK_SESSION_SECRET="dev_session_secret_change_me"
$env:STK_AGENT_TOKEN="dev_agent_token_change_me"
$env:STK_ORGANIZER_USERNAME="organizer"
$env:STK_ORGANIZER_PASSWORD="changeme_organizer"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Другие терминалы:

```powershell
cd apps/dashboard; npm run dev   # :5174 — /admin + /director
cd apps/overlay; npm run dev     # :5173 — overlay
# Agent Fake OBS (после создания матча):
cd apps/director-agent
# .env: STK_MATCH_ID, STK_AGENT_TOKEN, затем:
go run ./cmd/agent --fake-obs
```

Логин админа: `organizer` / `changeme_organizer`.

---

## Шаги

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `GET http://127.0.0.1:8000/health` | 200 |
| 2 | Admin: турнир → 4 команды → сетка → **Старт (Fake)** → скопировать ссылку режиссёра | Матч live; есть `match_id` |
| 3 | Открыть `/director/{matchId}` | Видны **Задержка Twitch** (hint + чек-лист RU) и **Состояние эфира** |
| 4 | Пока Agent не запущен | Health: агент/OBS «Нет связи»; понятная подсказка |
| 5 | Запустить Agent `--fake-obs` для этого матча | Через ~2 с agent+OBS **В порядке** / `connected` |
| 6 | `GET /api/v1/matches/{id}/health` | `overall` осмысленный; components platform/agent/obs/overlay/game |
| 7 | Сменить сцены: waiting → intro → teams → ingame → break → winner | Desired меняется; в **Журнале** появляется «Смена сцены» |
| 8 | Overlay: `/overlay/{matchId}` — переключить сцены с director | Все 6 layout’ов читаемы; watermark STK; branding если задан |
| 9 | Override имён/счёта на director | Overlay обновляется; в журнале «Override overlay» |
| 10 | (Опционально) судья: review-request | В журнале «Запрос разбора» |
| 11 | `.\scripts\verify.ps1` | **VERIFY OK — TZ006** |

### Быстрая проверка API

```powershell
# health
curl -s http://127.0.0.1:8000/api/v1/matches/<matchId>/health
# audit (публичное чтение)
curl -s http://127.0.0.1:8000/api/v1/matches/<matchId>/audit
```

---

## Блокеры / notes

| Тема | Статус GATE |
|------|-------------|
| Fake OBS + Fake match | **достаточен** |
| OBS Stream Delay checklist (без автонастройки) | **в GATE** |
| Реальный Twitch + Stream Delay | `live_twitch=blocked` (optional owner) |
| Live CS2 / WebRTC | blocked (наследование) |
| FFmpeg delay | вне scope (ADR-024 v2) |

**Критерий:** шаги 1–11 без устных пояснений разработчика ≤ 25 мин.
