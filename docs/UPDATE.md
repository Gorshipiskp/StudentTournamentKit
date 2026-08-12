# Обновление стенда — `git pull` и дальше

> Кому: владелец стенда после смены кода в репозитории.  
> Вход: [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md).  
> Секреты только в `.env` на машине — **не** коммить и не копируй в чат (Frozen F2).

Цель: после `git pull` стенд снова поднимается предсказуемо — без сюрпризов со схемой БД и optional-сервисами.

---

## Когда что поднимать (Compose profiles)

| Profile | Сервис | Нужен когда |
|---------|--------|-------------|
| *(без profile)* | mysql · api · nginx | Локальный Compose-стек (офлайн / CI без облака) |
| `webrtc` | coturn | Legacy Fake P2P `/watch?media=fake` с TURN; People Slice |
| `whip` | mediamtx | **Канон комментаторов:** OBS WHIP → `/watch` WHEP |

Fake primary (день матча без живого видео) — MediaMTX и coturn **не обязательны**.  
Live комментаторы — только `whip` (+ переменные MediaMTX в `.env`).

```powershell
# из корня репо
docker compose --env-file .env -f infra/platform/docker-compose.yml up -d
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile webrtc up -d
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx
```

Подробнее: [infra/platform/README](../infra/platform/README.md) · [infra/mediamtx/README](../mediamtx/README.md).

---

## Чеклист обновления (dev / стенд владельца)

Делай по порядку. Шаги со звёздочкой (*) — только если этот слой у тебя в работе.

1. **Останови** процессы, которые держат код/порты: API (uvicorn), Agent, по желанию frontend `npm run dev`. Compose-сервисы можно оставить, если менялся только код API на хосте.
2. **`git pull`** в корне репозитория (ветка, с которой работаешь). Не коммить `.env`.
3. **Зависимости** (если lockfile/go.mod менялись):
   - API: `apps/api` → venv → `pip install -r requirements.txt` (или как принято у вас)
   - Agent: `cd apps/director-agent` → при необходимости `go mod download`
   - Frontend: `npm ci` / `npm install` в overlay / dashboard / judge — только если обновляешь UI
4. **Миграции БД** (обязательно, если появились файлы в `apps/api/alembic/versions/`):

   ```powershell
   cd apps/api
   # корневой .env с MYSQL_* уже загружен в сессию или через ваш скрипт
   python -m alembic upgrade head
   ```

   Скрипты: `.\scripts\dev-remote.ps1` (migrate по умолчанию) · `.\scripts\alpha-dry-run.ps1 -Migrate` · `live-cs2-local.ps1` (тоже migrate, есть `-SkipMigrate`).
5. **Compose (*)** — если нужен локальный mysql/nginx или профили:
   - default / `webrtc` / `whip` — см. таблицу выше  
   - При remote MySQL у владельца **не** поднимай контейнер `api` из Compose (API с хоста) — [platform README](../infra/platform/README.md).
6. **Запусти снова:**
   - API: uvicorn или `.\scripts\dev-remote.ps1`
   - Agent: тот же матч / токен; Fake → `--fake-obs`; live сцены → без fake; **не** `--live-webrtc` для канона WHIP
   - MediaMTX (*) если комментаторы WHIP: `--profile whip`
7. **Проверка:**
   - `http://127.0.0.1:8000/health`
   - `http://127.0.0.1:8000/ready` (БД)
   - По желанию: `.\scripts\verify.ps1` (Fake GATE, без живого OBS)

---

## Что не коммитить

| Файл / путь | Почему |
|-------------|--------|
| `.env` | Пароли, токены Agent / WHIP HMAC / MySQL |
| Локальные demo `*.dem`, кэши, бинарники Agent | Артефакты машины |
| Секреты в WORKLOG / чат | F2 |

Схема переменных без секретов: [`.env.example`](../.env.example) (скопируй в `.env` и заполни у себя).

---

## Типичные сюрпризы

| Симптом | Действие |
|---------|----------|
| API падает на старте / pytest про БД | `alembic upgrade head` на ту же БД, что в `.env` |
| `/watch` WHIP «не стримит» после pull | Поднят ли `mediamtx`? Актуален ли `MEDIAMTX_*` в `.env`? |
| Agent не коннектится | Тот же `STK_AGENT_TOKEN` / match id, что в Platform |
| Compose «не видит» mediamtx | Нужен `--profile whip` |

Сбои в день матча (не про обновление кода): [PRODUCTION-RECOVERY.md](PRODUCTION-RECOVERY.md).

---

## VPS / прод-деплой

Авто-деплой и SSH на VPS — только **@owner** / devops по запросу. Этот документ — путь **git pull на стенде разработки и репетиции**, не Kubernetes и не Terraform.
