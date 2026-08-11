# Fake CS2 — локальный игровой контур без VPS

Имитатор CS2 + STP.Bridge для **Game Slice**: шлёт нормализованные события на Platform,
принимает команды `PauseMatch` / `ResumeMatch` / `ForfeitMatch` / `GetSnapshot` / `LoadMatch`,
отдаёт snapshot и ack.

Контракт: [`infra/game-server/CONTRACT.md`](../../infra/game-server/CONTRACT.md).

---

## Быстрый старт

```powershell
cd tools/fake-cs2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Самопроверка (Platform не нужна)
.\.venv\Scripts\python.exe -m fake_cs2 self-test

# Pytest
.\.venv\Scripts\python.exe -m pytest -q
```

---

## Против local Platform

Ожидаемый ingest (появится в TZ002 P2):

`POST http://127.0.0.1:8000/api/v1/internal/cs2/events`

До P2 ответ может быть **404** или connection refused — это нормально для P1.
Fake всё равно подписывает тело HMAC и пишет событие в stdout/файл при `--dry-run` / `--events-log`.

```powershell
# Терминал 1 — слушатель команд (health / commands / snapshot)
.\.venv\Scripts\python.exe -m fake_cs2 run `
  --platform-url http://127.0.0.1:8000 `
  --match-id m_dev `
  --server-id srv_fake `
  --webhook-secret dev_webhook_secret_change_me `
  --listen-port 27099

# Терминал 2 — пробный POST (404 OK до P2)
.\.venv\Scripts\python.exe -m fake_cs2 post-probe `
  --platform-url http://127.0.0.1:8000 `
  --webhook-secret dev_webhook_secret_change_me

# Сымитировать 2 раунда (POST на Platform; или добавь --dry-run)
.\.venv\Scripts\python.exe -m fake_cs2 emit-rounds --count 2 --dry-run
```

Проверки Fake:

```powershell
curl http://127.0.0.1:27099/health
curl http://127.0.0.1:27099/v1/snapshot
```

Пример команды паузы:

```powershell
curl -Method POST http://127.0.0.1:27099/v1/commands `
  -ContentType "application/json" `
  -Body '{"command_id":"c-pause-1","type":"PauseMatch","match_id":"m_dev","payload":{}}'
```

---

## Конфиг (env)

| Переменная | По умолчанию |
|------------|----------------|
| `FAKE_CS2_PLATFORM_URL` | `http://127.0.0.1:8000` |
| `FAKE_CS2_MATCH_ID` | `m_dev` |
| `FAKE_CS2_SERVER_ID` | `srv_fake` |
| `FAKE_CS2_WEBHOOK_SECRET` | `dev_webhook_secret_change_me` |
| `FAKE_CS2_LISTEN_HOST` | `127.0.0.1` |
| `FAKE_CS2_LISTEN_PORT` | `27099` |
| `FAKE_CS2_MAP` | `de_mirage` |
| `FAKE_CS2_DRY_RUN` | `false` |
| `FAKE_CS2_EVENTS_LOG` | (пусто) путь к JSONL |

---

## HTTP API Fake

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/health` | Жив ли процесс |
| GET | `/v1/snapshot` | Текущий snapshot |
| POST | `/v1/commands` | Whitelist-команды + ack |

Исходящие события → `POST {platform}/api/v1/internal/cs2/events` с заголовками:

- `X-STP-Signature: sha256=…`
- `X-STP-Event-Id: …`
- `X-STP-Protocol-Version: 1`

---

## Что не входит (следующие промпты)

- Match FSM / ingest на Platform (P2)
- Judge UI
- Живой CS2 / Bridge C#
