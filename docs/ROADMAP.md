# StudentTournamentKit — Roadmap

> Вертикальные срезы · не MVP-заглушки.  
> Обновлено: 2026-08-12.

---

## Этапы

| Этап | Название | Цель | Критерий готовности |
|------|----------|------|---------------------|
| **0** | Foundation | Документация, каркас репо, deploy skeleton | ARCHITECTURE + compose + `/health`/`/ready` + outbox + `scripts/verify.ps1` |
| **1** | Game Slice | CS2 server + adapter + match lifecycle | Тестовый 5v5 на VPS; pause/forfeit через API; GOTV demo saved |
| **2** | Production Slice | Director dashboard + OBS + overlay | Один ноутбук: сцены из панели, overlay live, watermark |
| **3** | People Slice | Judge + commentators | Mobile judge + WebRTC; канон комментаторов → `live_whip` (TZ011 gate_ready) |
| **4** | Tournament Slice | Bracket, admin UI, multi-tournament | Организатор без IT создаёт турнир; single elim; parallel tournaments |
| **5** | Broadcast Slice | Delayed Twitch, polish | OBS Stream Delay; semi-pro scenes; status dashboard |
| **6** | Tournament Alpha | Первый реальный турнир (внутренний) | Полный дистанционный турнир end-to-end |
| **7** | Production Ready | Стабильность, runbooks, docs | TZ010; повторный турнир за часы |
| **8** | BestTvGU API | Публичный read API | Документированный API для виджетов (без UI в STK) |

---

## Этап 0 — Foundation

- [x] Bootstrap ИИ-команды
- [x] VISION, ARCHITECTURE, DECISIONS, ROADMAP
- [x] Структура `apps/`, `infra/`, `scripts/`
- [x] Docker Compose skeleton (platform: api + mysql + nginx)
- [x] CI / verify script skeleton (`scripts/verify.ps1`)
- [x] FastAPI `/health` + `/ready`, Alembic foundation tables, outbox + correlation_id (TZ001 GATE)

**Следующий:** Этап 1 — Game Slice (закрыт; см. ниже).

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
**ТЗ:** [tasks/003_PRODUCTION-SLICE.md](../tasks/003_PRODUCTION-SLICE.md) · ранбук M=7.  
**Статус:** GATE **closed** (2026-08-12) на Fake OBS; live OBS optional.

| Deliverable | Описание | Статус |
|-------------|----------|--------|
| `apps/overlay/` | Svelte overlay, WebSocket, watermark | done |
| `apps/dashboard/` | Scene control, overlay override (`/director/`) | done |
| `apps/director-agent/` | OBS WebSocket / `--fake-obs`, platform WS | done |
| OBS templates | `apps/director-agent/templates/` + Stream Delay checklist | done |
| `docs/OVERLAY-CONTRACT.md` | snapshot + production + Agent messages | done |
| Owner smoke | `workers/developer/notes/TZ003-OWNER-SMOKE.md` | done |
| `scripts/verify.ps1` | TZ003 steps (api + FE build + go test) | done |

**Gate:** Режиссёр на одном ноутбуке ведёт тестовый матч с overlay и сценами из панели (Fake OBS допустим) — **выполнено**.

**Failure B** (Agent restart): reconciler A12 в `apps/director-agent` (+ pytest pointer в `test_failures_a_e.py`).

**Следующий:** Этап 3 — People Slice (TZ004).

---

## Этап 3 — People Slice

**Фокус:** Судья и комментаторы.  
**ТЗ:** [tasks/004_PEOPLE-SLICE.md](../tasks/004_PEOPLE-SLICE.md) · ранбук M=7.  
**Статус:** **GATE closed** (S005, 2026-08-12). Optional live: `live_webrtc=done` (TZ008, deprecated) · **`live_whip` gate_ready** (TZ011, 2026-08-12) — owner smoke → `live_whip=done`.

| Deliverable | Описание | GATE |
|-------------|----------|------|
| Invites | judge / commentator scoped tokens | done |
| `apps/judge/` | Mobile web, review workflow | done |
| Commentator `/watch` | WebRTC + TURN + invite | done (fake-webrtc) |
| Agent publisher | `--fake-webrtc` primary; Virtual Cam optional | done (fake) |
| Notifications | Tech pause → judge + watch + overlay | done |

**Gate (primary):** Judge UI + `/watch` video (fake-webrtc) + tech-pause sync — **closed**.  
**Gate (live WebRTC/OBS cam):** ✅ **done** — TZ008 (2026-08-12 @owner: real OBS + `/watch`).  
ТЗ: [tasks/008_LIVE-WEBRTC.md](../tasks/008_LIVE-WEBRTC.md).
Owner smoke: [TZ004-OWNER-SMOKE.md](../workers/developer/notes/TZ004-OWNER-SMOKE.md).

**Следующий:** Этап 6 — Tournament Alpha (TZ007); этап 4–5 GATE closed.

---

## Этап 4 — Tournament Slice

**Фокус:** Организаторский UI, сетка, multi-tournament.  
**ТЗ:** [tasks/005_TOURNAMENT-SLICE.md](../tasks/005_TOURNAMENT-SLICE.md) · ранбук M=7.  
**Статус:** **GATE closed** (2026-08-12; Fake match; `live_cs2`/`live_webrtc` = blocked).

| Deliverable | Описание |
|-------------|----------|
| Tournament admin | Wizard, teams, manual single-elim bracket |
| Multi-tournament | Parallel tournaments on one instance |
| Branding | Logos/colors BLOB in MySQL → overlay |
| Invite links | Director, judge, commentator из admin UI |

**Gate:** Нетехнический организатор создаёт турнир и проводит Fake-матч без правки конфигов. ✅

**Следующий:** Этап 6 — Tournament Alpha (TZ007); этап 5 GATE closed.

---

## Этап 5 — Broadcast Slice

**Фокус:** Полупро эфир, delay, мониторинг.  
**ТЗ:** [tasks/006_BROADCAST-SLICE.md](../tasks/006_BROADCAST-SLICE.md) · ранбук M=7.  
**Статус:** **GATE closed** (2026-08-12; Fake OBS; `live_twitch=blocked`).

| Deliverable | Описание | GATE |
|-------------|----------|------|
| Delay pipeline | OBS Stream Delay checklist + tournament delay hint (ADR-024 v1) | done |
| Scene polish | waiting/intro/teams/ingame/break/winner layouts + branding | done |
| Health dashboard | `GET /matches/{id}/health` + director panel | done |
| Match audit log | Persist + director UI | done |

**Gate:** Fake OBS smoke; overlay semi-pro; health + audit. ✅ Twitch live optional.

**Следующий:** Этап 6 — Tournament Alpha (TZ007).

---

## Этап 6 — Tournament Alpha

**Фокус:** Первый реальный дистанционный турнир.  
**ТЗ:** [tasks/007_TOURNAMENT-ALPHA.md](../tasks/007_TOURNAMENT-ALPHA.md) · ранбук M=6.  
**Статус:** gate_ready (S008) — Fake verify + dry-run OK; @owner smoke/post-mortem pending.

- Минимум 4 команды (single-elim)
- Полный цикл: создание → матчи → эфир → результаты
- Post-mortem + чеклист @owner
- Артефакты: [ALPHA-RUNBOOK](ALPHA-RUNBOOK.md) · [alpha-dry-run](../scripts/alpha-dry-run.ps1) · [docs/alpha/](alpha/) · [ALPHA-LIVE-TRACKS](ALPHA-LIVE-TRACKS.md)

**Gate:** `alpha-dry-run` + OWNER-SMOKE на Fake; live-треки optional (**blocked**).  
**Не:** production ready (это этап 7 / **TZ010**).

---

## Этап 7 — Production Ready

- Runbooks для организатора — hub: [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md)
- Failure recovery tested — human: [PRODUCTION-RECOVERY.md](PRODUCTION-RECOVERY.md); A–E tests green; B = Agent reconciler
- `git pull` update documented — [UPDATE.md](UPDATE.md)
- Второй турнир быстрее первого — чеклист в [PRODUCTION-RUNBOOK](PRODUCTION-RUNBOOK.md) · smoke [TZ010-OWNER-SMOKE](../workers/developer/notes/TZ010-OWNER-SMOKE.md) (**gate_ready**)

**ТЗ:** [010_PRODUCTION-READY.md](../tasks/010_PRODUCTION-READY.md) · ранбук [TZ010-PROMPT-RUNBOOK](../workers/developer/notes/TZ010-PROMPT-RUNBOOK.md) · статус: **gate_ready** (ждёт @owner).

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

1. **@owner** — [TZ010-OWNER-SMOKE](../workers/developer/notes/TZ010-OWNER-SMOKE.md) → `production_ready=done`.  
2. **@owner** — TZ011 / TZ009 live smokes (если ещё open).  
3. **TL** — live Twitch или этап 8 BestTvGU.  
4. Коммиты — только @owner.
