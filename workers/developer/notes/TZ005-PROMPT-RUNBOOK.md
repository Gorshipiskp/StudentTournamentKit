# TZ005 — PROMPT RUNBOOK · Tournament Slice

> ТЗ: [tasks/005_TOURNAMENT-SLICE.md](../../../tasks/005_TOURNAMENT-SLICE.md)  
> База: TZ001–004 GATE (Foundation → People; live CS2/WebRTC optional)  
> **M = 7** · P7 = GATE · 1 чат = 1 промпт  
> Философия: минимум промптов → максимум автономии (вертикали, не «слой за слоем»)

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/7 | Organizer auth + tournament CRUD (API + `/admin` list) | done | 2026-08-12 |
| 2/7 | Teams + players (API + admin UI) | done | 2026-08-12 |
| 3/7 | Single-elim bracket + match nodes (API + UI) | done | 2026-08-12 |
| 4/7 | Branding BLOBs → overlay snapshot | done | 2026-08-12 |
| 5/7 | Publish + start match + invite links из admin | done | 2026-08-12 |
| 6/7 | Multi-tournament smoke + wizard UX polish | done | WizardNav + empty states; multi-tournament smoke |
| 7/7 | verify + OWNER-SMOKE + GATE | done | VERIFY OK TZ005; OWNER-SMOKE; GATE closed |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/7 | §0 · §1 auth/tournaments · §2 F1 F8 F9 · §4 |
| 2/7 | §1 teams/players · §3 шаги 2–3 · ARCHITECTURE §8.2 |
| 3/7 | §1 bracket · §2 F3 F6 · §3 шаг 4 · ARCHITECTURE bracket_nodes |
| 4/7 | §1 branding · §2 F4 F7 · OVERLAY-CONTRACT |
| 5/7 | §1 invites/start · TZ004 invites · §3 шаг 5 |
| 6/7 | §1 multi-tournament · §3 · §0 цель |
| 7/7 | §3 · §5 Приёмка целиком |

---

## P1/7 — Organizer auth + tournament CRUD

### Делать

- Простой login организатора инстанса (env bootstrap password/secret → short-lived JWT/session)
- Защитить admin tournament endpoints; без auth → 401
- Расширить модель `tournaments`: `name`, `format` (`single_elim`), `status`, `settings_json` (в т.ч. `configured_broadcast_delay_seconds`)
- API: list / create / get / patch / publish (draft→published)
- `apps/dashboard`: route `/admin` — login + список турниров + «Создать»
- Alembic migration; pytest auth + CRUD
- Не ломать foundation probe / существующие Fake matches

### Не делать

- Teams/bracket UI (P2–P3)
- Branding (P4)
- Multi-user RBAC
- Коммит без @owner

### DoD

- [ ] Login → список → создать draft → publish
- [ ] Pytest зелёный на auth + CRUD
- [ ] Director `/director/:matchId` без регрессии

### Проверки

```text
POST /api/v1/auth/login → token
GET /api/v1/tournaments (401 без; 200 с)
POST create + POST publish
```

### После P

- WORKLOG; трекер P1=done; **новый чат** на P2

---

## P2/7 — Teams + players

### Делать

- Таблицы `teams`, `players` (+ domain/repos)
- API под tournament: CRUD teams, CRUD players
- Admin UI: экран команд турнира (добавить/переименовать/удалить; игроки)
- Валидации: уникальность имени в турнире; разумные лимиты размера
- Pytest

### Не делать

- Bracket (P3)
- Branding
- Steam auth / Discord

### DoD

- [ ] 4 команды с игроками через UI и API
- [ ] Второй турнир имеет изолированный набор команд

### Проверки

```text
POST .../tournaments/{id}/teams ×4
GET teams list scoped by tournament_id
```

### После P

- WORKLOG; трекер P2=done; новый чат P3

---

## P3/7 — Single-elim bracket + match nodes

### Делать

- `bracket_nodes`: round, position, team sources / winner-of, `match_id`
- API: generate empty bracket for N∈{4,8} (16 optional), PATCH slots (назначить team), GET tree
- При готовности пары — создать `Match` (существующий create_match) и связать `match_id`
- Admin UI: визуальная/табличная сетка, drag или select слотов
- Запрет ломать published/completed без явных правил (минимум: draft editable; published — только незапущенные слоты)

### Не делать

- Auto-seeding algorithms
- Double elim / Swiss
- Branding / invites UI

### DoD

- [ ] Сетка 4 команды → 3 матча (2 полуфинала + финал) с `match_id` где пара полная
- [ ] Pytest на generate + assign + match link

### Проверки

```text
POST bracket/generate?size=4
PATCH nodes with team_ids
GET bracket → matches linked
```

### После P

- WORKLOG; трекер P3=done; новый чат P4

---

## P4/7 — Branding → overlay

### Делать

- `tournament_branding`: logo_blob (≤2MB), colors_json; bg optional ≤5MB
- API upload/get branding (organizer auth)
- Merge в overlay snapshot: `branding.logo_url` или inline ref + colors
- Overlay UI: логотип/акцент без поломки watermark STK
- Admin UI: загрузить лого, выбрать 1–2 цвета
- Pytest merge + size reject

### Не делать

- Полный semi-pro motion redesign
- CDN; достаточно API-served asset URL

### DoD

- [ ] После upload GET overlay содержит branding
- [ ] Overlay build показывает лого/цвет
- [ ] Watermark STK остаётся

### Проверки

```text
PUT branding → GET overlay snapshot fields
npm run build apps/overlay
```

### После P

- WORKLOG; трекер P4=done; новый чат P5

---

## P5/7 — Publish ops: start match + invites

### Делать

- Из admin на узле/матче: «Старт» (вызов существующего start + Fake path документирован)
- UI: сгенерировать/показать invite-ссылки judge, commentator; ссылка на director dashboard
- Deep-link копирование одним кликом (RU copy)
- Не ломать TZ004 redeem/judge/watch
- Pytest или integration: create invite from organizer session for match

### Не делать

- Live CS2 deploy
- Broadcast delay automation
- Новый signaling

### DoD

- [ ] Организатор без CLI получает все ссылки для одного матча
- [ ] Judge redeem + Fake review path всё ещё работает
- [ ] Director page открывается по ссылке из admin

### Проверки

```text
Admin → match → invites → open judge URL → status OK
```

### После P

- WORKLOG; трекер P5=done; новый чат P6

---

## P6/7 — Multi-tournament + wizard polish

### Делать

- Сквозной wizard UX: шаги понятны нетехническому человеку (RU глаголы)
- Smoke: два published турнира параллельно; матчи/инвайты не пересекаются
- Пустые/ошибочные состояния (нет команд, неполная сетка) — ясные сообщения
- Короткая инструкция `apps/dashboard/README.md` § admin
- Регрессия: overlay/judge/director smoke sanity

### Не делать

- Новые форматы сетки
- BestTvGU API
- Коммит без @owner

### DoD

- [ ] Owner может пройти путь «создать → команды → сетка → старт → ссылки» без подсказок разработчика (черновик smoke)
- [ ] 2 турнира на инстансе OK

### После P

- WORKLOG; трекер P6=done; новый чат P7

---

## P7/7 — verify + OWNER-SMOKE + GATE

### Делать

- `scripts/verify.ps1` — шаги TZ005 (api tests + dashboard build)
- `workers/developer/notes/TZ005-OWNER-SMOKE.md` (≤25 мин, Fake only)
- Пройти primary GATE чеклист ТЗ §5; отметить в ТЗ
- Обновить: трекер all done; `tasks/005` статус; CURRENT_TASK; WORKLOG; CODE_CHANGE_BOARD; журнал CURRENT
- ROADMAP этап 4 чеклист

### Не делать

- Scope creep Broadcast / Alpha
- Требовать live CS2 / live WebRTC для GATE

### DoD

- [ ] verify зелёный
- [ ] OWNER-SMOKE написан; primary GATE closed (или явно `blocked` с причиной)
- [ ] Команда знает: следующий = TZ006 Broadcast

### Проверки

```text
pwsh scripts/verify.ps1
# пройти TZ005-OWNER-SMOKE.md
```

### После P

- GATE closed → Team Lead открывает Broadcast Slice

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/7 из TZ005-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
