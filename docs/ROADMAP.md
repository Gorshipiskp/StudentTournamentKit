# StudentTournamentKit — Roadmap

> Вертикальные срезы · не MVP-заглушки.  
> Обновлено: 2026-08-11.

---

## Этапы

| Этап | Название | Цель | Критерий готовности |
|------|----------|------|---------------------|
| **0** | Foundation | Документация, каркас репо, deploy skeleton | ARCHITECTURE + compose + `/health`/`/ready` + outbox + `scripts/verify.ps1` |
| **1** | Game Slice | CS2 server + adapter + match lifecycle | Тестовый 5v5 на VPS; pause/forfeit через API; GOTV demo saved |
| **2** | Production Slice | Director dashboard + OBS + overlay | Один ноутбук: сцены из панели, overlay live, watermark |
| **3** | People Slice | Judge + commentators | Mobile judge workflow; 1–2 комментатора в браузере WebRTC |
| **4** | Tournament Slice | Bracket, admin UI, multi-tournament | Организатор без IT создаёт турнир; single elim; parallel tournaments |
| **5** | Broadcast Slice | Delayed Twitch, polish | OBS Stream Delay; semi-pro scenes; status dashboard |
| **6** | Tournament Alpha | Первый реальный турнир (внутренний) | Полный дистанционный турнир end-to-end |
| **7** | Production Ready | Стабильность, runbooks, docs | Повторный турнир за часы; documented failure recovery |
| **8** | BestTvGU API | Публичный read API | Документированный API для виджетов (без UI в STK) |

---

## Этап 0 — Foundation

- [x] Bootstrap ИИ-команды
- [x] VISION, ARCHITECTURE, DECISIONS, ROADMAP
- [x] Структура `apps/`, `infra/`, `scripts/`
- [x] Docker Compose skeleton (platform: api + mysql + nginx)
- [x] CI / verify script skeleton (`scripts/verify.ps1`)
- [x] FastAPI `/health` + `/ready`, Alembic foundation tables, outbox + correlation_id (TZ001 GATE)

**Следующий:** Этап 2 — Production Slice (**TZ003**); этап 1 primary GATE closed (live VPS optional).

---

## Этап 1 — Game Slice

**Фокус:** CS2 contract, Fake Game Server, Match/Judge API, STK.Bridge skeleton, deploy-cs2.

| Deliverable | Описание |
|-------------|----------|
| Contract + Fake CS2 | Webhooks/commands/snapshot без живого VPS |
| `apps/api/` adapter | Ingest, FSM, judge, commands, reconcile |
| `STK.Bridge` | Skeleton CounterStrikeSharp |
| `scripts/deploy-cs2.sh` | Install path для VPS |
| Demo durable stub | Не только ephemeral disk |

**Gate (primary):** Fake end-to-end + tests A–E + Bridge/deploy artifacts.  
**Gate (live):** optional 5v5 when VPS available — see [tasks/002_GAME-SLICE.md](../tasks/002_GAME-SLICE.md) §5.

### Чеклист primary (TZ002 GATE, 2026-08-11)

- [x] Contract + Fake CS2
- [x] Ingest → Match FSM + commands + judge review (Fake)
- [x] Registry + snapshot reconcile
- [x] Failure A–E (`apps/api/tests/test_failures_a_e.py`; B = skip → Production)
- [x] STK.Bridge skeleton (build blocked без `dotnet` — documented)
- [x] `deploy-cs2` + demo durable stub
- [x] `scripts/verify.ps1` зелёный
- [ ] Live smoke — **blocked** (нет VPS / `@owner` SSH)

**Статус этапа 1:** primary GATE **closed** на Fake; live — когда будет VPS.

---

## Этап 2 — Production Slice

**Фокус:** Overlay + dashboard + OBS + Director Agent.

| Deliverable | Описание |
|-------------|----------|
| `apps/overlay/` | Svelte overlay, WebSocket, watermark |
| `apps/dashboard/` | Scene control, match control, overlay override |
| `apps/director-agent/` | OBS WebSocket, platform connection |
| OBS templates | Per-tournament scene collection export |

**Gate:** Режиссёр на одном ноутбуке ведёт тестовый матч с overlay и сценами из панели.

---

## Этап 3 — People Slice

**Фокус:** Судья и комментаторы.

| Deliverable | Описание |
|-------------|----------|
| `apps/judge/` | Mobile web, review workflow |
| Commentator viewer | WebRTC + TURN + invite links |
| Notifications | Tech pause → director + commentators + overlay |

**Gate:** Полный workflow судьи на тестовом матче; 1–2 комментатора с live video в браузере.

---

## Этап 4 — Tournament Slice

**Фокус:** Организаторский UI, сетка, multi-tournament.

| Deliverable | Описание |
|-------------|----------|
| Tournament admin | Wizard, teams, manual bracket |
| Multi-tournament | Parallel tournaments on one instance |
| Branding | Logos/colors BLOB in MySQL |
| Invite links | Director, judge, commentator |

**Gate:** Нетехнический организатор создаёт турнир и проводит матч без правки конфигов.

---

## Этап 5 — Broadcast Slice

**Фокус:** Полупро эфир, delay, мониторинг.

| Deliverable | Описание |
|-------------|----------|
| Delay pipeline | **OBS Stream Delay** ~90–120 с (чек-лист из настроек турнира); FFmpeg в Agent — только если понадобится (v2) |
| Scene polish | Intro, teams, break, winner, transitions |
| Health dashboard | CS2, platform, agent, overlay, OBS |
| Match audit log | UI for match actions |

**Gate:** Тестовый эфир на Twitch с delay; semi-pro вид.

---

## Этап 6 — Tournament Alpha

**Фокус:** Первый реальный дистанционный турнир.

- Минимум 4 команды (или по ситуации)
- Полный цикл: создание → матчи → эфир → результаты
- Post-mortem документ

**Gate:** Владелец принимает по чеклисту.

---

## Этап 7 — Production Ready

- Runbooks для организатора
- Failure recovery tested
- `git pull` update documented
- Второй турнир быстрее первого

---

## Этап 8 — BestTvGU API (когда StudentTournamentKit стабилен)

- Public read API documented
- API keys per organizer
- Владелец передаёт спецификацию тимлиду BestTvGU

---

## Не в roadmap

- Другие игры
- Мобильное приложение
- Kubernetes
- Player stream integration for judge
- Faceit / betting
- SaaS multi-tenant (сейчас: instance per organizer)

---

## Следующий шаг

**Этап 2 / TZ003 Production Slice** — overlay + dashboard + Director Agent + OBS.  
Live CS2 smoke (этап 1) — когда `@owner` даст VPS; иначе остаётся `live_smoke=blocked`.
