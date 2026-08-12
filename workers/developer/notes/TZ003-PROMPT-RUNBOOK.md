# TZ003 — PROMPT RUNBOOK · Production Slice

> ТЗ: [tasks/003_PRODUCTION-SLICE.md](../../../tasks/003_PRODUCTION-SLICE.md)  
> База: TZ001 Foundation + TZ002 Game Slice (primary GATE)  
> **M = 7** · P7 = GATE · 1 чат = 1 промпт  
> Философия: минимум промптов → максимум автономии (вертикали, не «слой за слоем»)

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/7 | Контракт overlay+production + Platform snapshot/WS | done | 2026-08-11 |
| 2/7 | Overlay Svelte (Browser Source + watermark) | done | 2026-08-11 |
| 3/7 | Production desired API + Agent session WS (без OBS) | done | 2026-08-11 |
| 4/7 | Director Agent ↔ OBS (или Fake OBS) reconcile | done | 2026-08-11 |
| 5/7 | Dashboard режиссёра: сцены + статус + override UI | done | 2026-08-11 |
| 6/7 | OBS template stub + Agent README/run | done | 2026-08-12 |
| 7/7 | verify + OWNER-SMOKE + GATE | done | 2026-08-12 |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать из ТЗ / docs |
|---|---------------------|
| 1/7 | §0 · §1 snapshot/WS · §2 F2 F5 F6 · §4 · INVARIANTS §8 |
| 2/7 | §0 overlay · §2 F4 · ARCHITECTURE §7.3 · LAYERS §5 |
| 3/7 | §2 F1 F3 · §4 production API · INVARIANTS §3.3 §7 |
| 4/7 | §2 F1 F3 F7 · ADR-021 · LAYERS §6 · A8 A12 |
| 5/7 | §0 dashboard · §2 F1 · §3 To-be · ARCHITECTURE §7.2 |
| 6/7 | §1 templates · §4 OBS template path |
| 7/7 | §3 · §5 Приёмка целиком |

---

## P1/7 — Контракт + Platform overlay snapshot / WS

### Делать

- Короткий контракт: `docs/OVERLAY-CONTRACT.md` (или `PRODUCTION-CONTRACT.md`):
  - `overlay.snapshot` JSON shape, `protocol`, `version` per match
  - production desired/actual fields (scene, agent_status, obs_status)
  - Agent WS message types (минимум)
- Domain/application: merge game view → overlay snapshot; persist `overlay_revision`
- `GET /api/v1/matches/{id}/overlay`
- `WS /ws/overlay/{matchId}` — на connect и на update слать full snapshot
- Подписка на match score/status из TZ002 (Fake events уже есть) → bump version + broadcast
- Pytest: snapshot version++, WS или service-level push

### Не делать

- Красивый Svelte UI (P2)
- Director Agent / OBS (P3–P4)
- Dashboard (P5)
- Коммит без @owner

### DoD

- [x] Контракт в репо
- [x] GET overlay отдаёт snapshot с version
- [x] После Fake score event version растёт (тест)
- [x] WS reconnect → полный snapshot (тест или явная проверка)

### Проверки

```text
# Fake match + event → GET overlay version N
# WS client receives overlay.snapshot
```

### После P

- WORKLOG; трекер P1=done; **новый чат** на P2

---

## P2/7 — Overlay Svelte (Browser Source + watermark)

### Делать

- Поднять `apps/overlay/` (Svelte + Vite): route `/overlay/[matchId]`
- Подключение к Platform WS; рендер счёта/команд/сцены из snapshot
- **Watermark STP** всегда видим (угол, едва заметный — по продукту)
- Dev README: URL для OBS Browser Source; CORS/nginx static заготовка ок
- Smoke: ручной или playwright/light test не обязателен — достаточно скрипта/README + unit на parse snapshot

### Не делать

- Production/Agent
- Dashboard
- Полный semi-pro motion design (достаточно читаемого эфира)
- Коммит без @owner

### DoD

- [x] `npm run build` (или pnpm) успешен
- [x] В браузере overlay показывает данные snapshot + watermark
- [x] Reconnect WS не ломает UI (полный snapshot)

### Проверки

```text
cd apps/overlay && npm install && npm run build
# open overlay URL against local API
```

### После P

- WORKLOG; P2=done; новый чат P3

---

## P3/7 — Production desired API + Agent session WS

### Делать

- Domain production: desired.scene, agent_status, obs_status (без OBS SDK)
- `GET/PATCH /api/v1/matches/{id}/production` — смена desired.scene
- Outbox → notify agent / overlay по необходимости
- Platform WS канал для Agent: auth stub (token/env), push desired, принимать actual report
- Без реального OBS: Agent можно ещё не писать — достаточно **API + контракт сообщений** и test double «fake agent client» в pytest

### Не делать

- Go Agent binary (P4)
- Dashboard UI (P5)
- Коммит без @owner

### DoD

- [x] PATCH production меняет desired в DB
- [x] Fake agent client получает desired после PATCH (тест)
- [x] Dashboard ещё не обязателен — curl достаточен

### Проверки

```text
curl PATCH .../production { "desired_scene": "intro" }
# test: fake agent saw desired
```

### После P

- WORKLOG; P3=done; новый чат P4

---

## P4/7 — Director Agent ↔ OBS (или Fake OBS)

### Делать

- `apps/director-agent/` на Go (ADR-021): connect Platform WS, apply desired.scene
- OBS WebSocket v5 client **или** встроенный `--fake-obs` для CI/GATE без установки OBS
- Reconcile loop: desired ≠ actual → SetCurrentProgramScene; report actual
- Failure B из TZ002: Agent restart → apply desired, не replay command history (A12)
- Pytest/Go test + опционально e2e с fake-obs

### Не делать

- WebRTC / Pion publish (People Slice)
- FFmpeg delay (ADR-024 v2)
- Dashboard (P5)
- Коммит без @owner

### DoD

- [x] Agent стартует с README-командой
- [x] При смене desired сцена actual обновляется (fake-obs или реальный OBS)
- [x] Restart Agent → снова desired без падения
- [x] Нет OBS-клиента в dashboard коде (grep)

### Проверки

```text
# agent --fake-obs --platform ws://...
# PATCH production → agent log/actual matches
```

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/7 — Dashboard режиссёра

### Делать

- `apps/dashboard/`: маршрут `/director/[matchId]`
- UI: кнопки сцен, статус match/score (TZ002 API), agent/OBS status, простая форма overlay override
- Только HTTP/WS к **Platform** — никогда к OBS
- Nginx/static: отдача build dashboard (dev proxy ок)

### Не делать

- Organizer wizard / bracket editor
- Judge UI
- Коммит без @owner

### DoD

- [x] Из UI меняется desired.scene (видно в API)
- [x] Override уходит в Platform и отражается на overlay
- [x] Build проходит

### Проверки

```text
cd apps/dashboard && npm run build
# manual: director page → scene + override
```

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/7 — OBS template stub + Agent docs

### Делать

- Пример Scene Collection / список сцен + Browser Source URL placeholder
- README: как импортировать в OBS; Stream Delay чек-лист (без автоматизации)
- Agent: config example (`.env.example` локальный, gitignored secrets)
- Зафиксировать ports/URLs в `overview/code-map.md`

### Не делать

- Полный installer MSI (достаточно `go build` + README; installer — nice-to-have)
- People/WebRTC
- Коммит без @owner

### DoD

- [x] Template/docs в репо
- [x] Новый разработчик поднимает Agent+overlay по README без устных пояснений

### Проверки

```text
# readme path exists; template file exists
```

### После P

- WORKLOG; P6=done; новый чат P7 GATE

---

## P7/7 — verify + OWNER-SMOKE + GATE

### Делать

- `scripts/verify.ps1`: compose config + api pytest + (если есть) overlay/dashboard build или agent test
- `workers/developer/notes/TZ003-OWNER-SMOKE.md` — шаги ≤ 15 мин
- Пройти §5 ТЗ; отметить ROADMAP этап 2 чеклист
- Failure B закрыт смыслом (Agent restart) — сослаться в отчёте
- Краткий отчёт владельцу

### Не делать

- TZ004 / WebRTC
- Коммит без @owner
- Scope creep «ещё анимации»

### DoD (GATE)

- [x] Все пункты §5 ТЗ
- [x] Owner smoke выполним по инструкции
- [x] Трекер P1–P7 done
- [x] Явно: «TZ003 GATE готов» / блокеры (например: только fake-obs, без реального OBS)

### Owner smoke (черновик)

```text
1. compose up Platform
2. Fake match + score (TZ002)
3. overlay URL → watermark + score
4. agent --fake-obs (или OBS)
5. dashboard director → смена сцены
6. override overlay → видно в Browser Source
7. scripts/verify.ps1
```

---

## Эскалация

| Ситуация | Куда |
|----------|------|
| Нет Go на машине | Документировать blocker; CI/fake-obs; @devops |
| Нет OBS у владельца | GATE на `--fake-obs` достаточен; live OBS — optional note |
| Хочется WebRTC сейчас | Отклонить → TZ004 |
| Dashboard→OBS напрямую | Architectural bug (F1/A8) — откатить |
| Конфликт Frozen | @team-lead |

---

## Связь с TZ002

- Match/score/judge API и Fake CS2 — **переиспользовать**, не дублировать
- INVARIANTS failure **B** (Agent restart) закрывается в P4/P7
- `live_smoke` CS2 VPS остаётся optional/blocked вне этого ТЗ
