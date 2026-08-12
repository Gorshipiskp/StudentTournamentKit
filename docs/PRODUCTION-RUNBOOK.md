# Production runbook — день матча и второй турнир

> **Один вход** для организатора и владельца стенда после Alpha.  
> ТЗ: [tasks/010_PRODUCTION-READY.md](../tasks/010_PRODUCTION-READY.md) · этап roadmap 7.  
> Цель: следующий турнир — **за часы**, не за дни поиска по десяти файлам.

**Не это:** новые фичи эфира, Twitch GATE, Kubernetes.  
**Primary путь приёмки:** Fake (как Alpha). Живой CS2 / OBS WHIP — по желанию, см. live-треки.

---

## Оглавление (≤5 мин)

| Нужно | Открой |
|-------|--------|
| **Порядок дня матча (Fake)** | [§ День матча](#день-матча-fake--основной-путь) |
| **Ещё один турнир быстро** | [§ Второй турнир](#второй-турнир-за-часы) |
| Клики организатора | [alpha/organizer.md](alpha/organizer.md) |
| Режиссёр + Agent | [alpha/director.md](alpha/director.md) |
| Судья с телефона | [alpha/judge.md](alpha/judge.md) |
| **Второй турнир / Production Ready** | [TZ010-OWNER-SMOKE.md](../workers/developer/notes/TZ010-OWNER-SMOKE.md) |
| Репетиция Alpha (чеклист владельца) | [ALPHA-RUNBOOK.md](ALPHA-RUNBOOK.md) |
| Живой CS2 / WHIP / Twitch | [ALPHA-LIVE-TRACKS.md](ALPHA-LIVE-TRACKS.md) |
| Сбой «что делать» | [PRODUCTION-RECOVERY.md](PRODUCTION-RECOVERY.md) |
| Обновить стенд (`git pull`) | [UPDATE.md](UPDATE.md) |
| Автопроверка стенда | [`scripts/alpha-dry-run.ps1`](../scripts/alpha-dry-run.ps1) · [`verify.ps1`](../scripts/verify.ps1) |

Секреты и пароли — только в `.env` на машине; не в чат и не в git.

---

## День матча (Fake — основной путь)

Типичная последовательность. Детали кликов — в памятках ролей, не здесь.

| # | Кто | Что сделать | Готово, когда |
|---|-----|-------------|----------------|
| 1 | Владелец стенда | Поднять MySQL / API / dashboard / overlay / judge | `http://127.0.0.1:8000/health` отвечает |
| 2 | Организатор | Турнир → 4 команды → сетка → **Старт (Fake)** → скопировать ссылки | Матч live; ссылки ушли режиссёру и судье → [organizer.md](alpha/organizer.md) |
| 3 | Режиссёр | Панель + Agent с `--fake-obs` → сцены | «Состояние эфира» не «нет связи» → [director.md](alpha/director.md) |
| 4 | Судья | Invite → разбор → продолжить или тех. поражение | Матч не сломан → [judge.md](alpha/judge.md) |
| 5 | Кто угодно | Overlay `/overlay/{матч}` | Сцена и счёт читаемы |
| 6 | Владелец | По желанию: health матча и журнал действий | Смена сцен / судья видны в журнале |

Полный чеклист «день Alpha состоялся»: [ALPHA-RUNBOOK § приёмка](ALPHA-RUNBOOK.md#чеклист-приёмки-владельца-fake-e2e).  
Скрипт-напоминалка: `.\scripts\alpha-dry-run.ps1` (см. [scripts/README](../scripts/README.md)).

### Быстрые URL (локальный dev)

| Куда | Обычно |
|------|--------|
| Админка | `http://127.0.0.1:5174/admin` |
| Режиссёр | `http://127.0.0.1:5174/director/{matchId}` |
| Overlay | `http://127.0.0.1:5173/overlay/{matchId}` |
| Судья | invite из staff-ссылок (часто порт `:5175`) |
| API health | `http://127.0.0.1:8000/health` |

---

## Второй турнир (за часы)

Не начинай с поиска «как поднять Alpha с нуля». Если стенд уже работал — ориентир **≤ 45 мин** на весь drill (см. smoke).

### Чеклист (Fake)

| # | Шаг | Готово, когда |
|---|-----|----------------|
| 1 | Стенд жив: `http://127.0.0.1:8000/health` | 200; при сомнении — `verify.ps1` / `alpha-dry-run.ps1` |
| 2 | Админка → **новый** турнир → опубликовать | Не править сыгранный кубок «вслепую» |
| 3 | **4 команды** → **создать сетку** → слоты | У пар есть матчи |
| 4 | **Старт (Fake)** у первого матча | Новый `match_id` |
| 5 | **Ссылки для команды** — заново режиссёру и судье | Старые invite могут протухнуть |
| 6 | Agent на **новый** match id (`--fake-obs` на Fake) | «Состояние эфира» без «Нет связи» |
| 7 | Overlay `/overlay/{матч}` (+ `/watch` по желанию) | Сцена читаема |

Клики 2–5: [organizer.md](alpha/organizer.md).  
Режиссёр / судья: [director.md](alpha/director.md) · [judge.md](alpha/judge.md).  
**Timed приёмка владельца:** [TZ010-OWNER-SMOKE.md](../workers/developer/notes/TZ010-OWNER-SMOKE.md).

### Health в день матча (одна строка)

Смотри **«Состояние эфира»** на панели режиссёра и при необходимости `GET /api/v1/matches/{id}/health` — [BROADCAST-HEALTH.md](BROADCAST-HEALTH.md). Не нужен отдельный Prometheus.

---

## Live (не обязательно для Primary)

| Зачем | Трек | Куда |
|-------|------|------|
| Игровой сервер на машине владельца | `live_cs2_local` | [ALPHA-LIVE-TRACKS](ALPHA-LIVE-TRACKS.md) · [TZ009-OWNER-SMOKE](../workers/developer/notes/TZ009-OWNER-SMOKE.md) |
| Комментаторы в `/watch` (канон) | `live_whip` — OBS → MediaMTX → WHEP | [ALPHA-LIVE-TRACKS](ALPHA-LIVE-TRACKS.md) · [TZ011-OWNER-SMOKE](../workers/developer/notes/TZ011-OWNER-SMOKE.md) |
| Задержка на Twitch | `live_twitch` | [BROADCAST-DELAY](BROADCAST-DELAY.md) · ALPHA-LIVE |
| Старый Virtual Cam WebRTC | `live_webrtc` | **deprecated** — не для нового дня |

Канон комментаторов = **OBS WHIP**, не Virtual Cam / `--live-webrtc`.

---

## Роли — куда смотреть

| Роль | Памятка |
|------|---------|
| Организатор | [docs/alpha/organizer.md](alpha/organizer.md) |
| Режиссёр | [docs/alpha/director.md](alpha/director.md) |
| Судья | [docs/alpha/judge.md](alpha/judge.md) |
| Владелец (приёмка / post-mortem) | [ALPHA-RUNBOOK](ALPHA-RUNBOOK.md) · [POST-MORTEM](alpha/POST-MORTEM-TEMPLATE.md) |

---

## Что ещё допишется в этой волне

| Тема | Когда |
|------|--------|
| Таблица сбоев «симптом → действие» | **есть** — [PRODUCTION-RECOVERY.md](PRODUCTION-RECOVERY.md) |
| Обновление: `git pull` → migrate → compose profiles | **есть** — [UPDATE.md](UPDATE.md) |
| Owner smoke «второй турнир» | **gate_ready** — [TZ010-OWNER-SMOKE.md](../workers/developer/notes/TZ010-OWNER-SMOKE.md) (@owner → done) |

До тех пор не объявляй стенд «production ready» без прохождения [TZ010-OWNER-SMOKE](../workers/developer/notes/TZ010-OWNER-SMOKE.md) (@owner).
