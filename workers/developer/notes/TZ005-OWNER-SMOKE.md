# TZ005 — Owner smoke (≤ 25 мин)

> Tournament Slice GATE. **Fake match only** — без live CS2 VPS и без live WebRTC.  
> Admin: [apps/dashboard/README.md](../../../apps/dashboard/README.md) § «Admin: как провести турнир»  
> Ранбук: [TZ005-PROMPT-RUNBOOK.md](TZ005-PROMPT-RUNBOOK.md)

**Статус:** Primary GATE = organizer admin + 2 турнира + сетка + Fake start + staff links + branding → overlay.  
Наследует: `live_webrtc=blocked` (TZ004).

---

## Подготовка

```powershell
# Compose MySQL
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
$env:STK_DASHBOARD_ORIGIN="http://127.0.0.1:5174"
$env:STK_JUDGE_ORIGIN="http://127.0.0.1:5175"
$env:STK_WATCH_ORIGIN="http://127.0.0.1:5173"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Другие терминалы:

```powershell
cd apps/dashboard; npm run dev   # :5174 — /admin + /director
cd apps/overlay; npm run dev     # :5173 — overlay (+ /watch)
cd apps/judge; npm run dev       # :5175 — судья (опционально в этом smoke)
```

Логин админа: `organizer` / `changeme_organizer` (как в `.env.example`).

---

## Шаги

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `GET http://127.0.0.1:8000/health` | 200 |
| 2 | Открыть `http://127.0.0.1:5174/admin` → войти | Список турниров; без логина API 401 |
| 3 | Создать **два** черновика → **Опубликовать** оба | Два published турнира в списке |
| 4 | Турнир A: добавить **4** команды (+ по 1 игроку) | Подсказка «можно к сетке» |
| 5 | Турнир B: тоже 4 команды с **теми же именами**, что в A | Создаются; имена не конфликтуют между турнирами |
| 6 | Турнир A → **Сетка и старт** → создать сетку 4 → заполнить слоты | У узлов появляются матчи (`match_id`) |
| 7 | У первого матча: **Старт (Fake)** | Статус live; без CS2 VPS |
| 8 | **Ссылки для команды** → скопировать режиссёр / судья / комментатор | URL с токенами; режиссёр `/director/{matchId}` |
| 9 | Открыть `/director/{matchId}` по ссылке | Панель режиссёра видит матч |
| 10 | Турнир A → **Брендинг**: цвет accent (+ опционально лого) → сохранить | Успех; в overlay snapshot есть branding (или цвет на UI overlay) |
| 11 | Overlay: `http://127.0.0.1:5173/overlay/<matchId>` | Видны цвета/лого турнира; watermark STK на месте |
| 12 | `.\scripts\verify.ps1` | **VERIFY OK — TZ005** |

### Быстрая проверка API (если UI недоступен)

```powershell
# Логин
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"username\":\"organizer\",\"password\":\"changeme_organizer\"}"
# Дальше: Authorization: Bearer <access_token>
# POST /api/v1/tournaments → publish → teams → bracket/generate → patch nodes → matches/{id}/start → staff-links
```

Автоматический smoke изоляции: `pytest apps/api/tests/test_multi_tournament_smoke.py` (входит в `verify.ps1`).

---

## Блокеры / notes

| Тема | Статус GATE |
|------|-------------|
| Fake start матча | **достаточен** |
| Live CS2 VPS | вне TZ005 (optional) |
| Live WebRTC / OBS Virtual Cam | `live_webrtc=blocked` (TZ004) |
| Auto-seeding / double-elim | вне scope |
| Broadcast delay | TZ006 |

**Критерий:** шаги 1–12 без устных пояснений разработчика ≤ 25 мин.
