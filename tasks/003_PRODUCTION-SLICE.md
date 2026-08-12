# ТЗ 003 — Production Slice (overlay + режиссёр + OBS)

| Поле | Значение |
|------|----------|
| **Статус** | done (GATE 2026-08-12; Fake OBS) |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer (+ devops только при блокере Agent/installer) |
| **Этап roadmap** | 2 — Production Slice |
| **Предыдущий** | TZ002 Game Slice (primary GATE done; live VPS optional) |
| **Следующий** | TZ004 People Slice |

---

## 0. Цель (для людей)

Режиссёр на **одном ноутбуке** видит матч на overlay в OBS и **переключает сцены эфира из панели**, не лазая в OBS руками. Платформа отдаёт актуальный счёт/статус; агент на ноутбуке — единственный, кто трогает OBS.

---

## 1. Scope

**В scope:**

- Контракт realtime: `overlay.snapshot` (full state, `version` per match) + production desired/actual
- Platform: overlay merge (game state + manual override) → durable revision + WS fanout (single replica)
- `apps/overlay/` — Svelte: Browser Source URL, watermark STP всегда, счёт/команды/сцена
- `apps/dashboard/` — маршрут режиссёра: сцены, override overlay, статус матча/агента/OBS (читает Fake/match API из TZ002)
- `apps/director-agent/` — Go: WS к Platform, OBS WebSocket v5, reconcile desired.scene → actual
- Outbox → side effects `notify_overlay` / `notify_agent` (или эквивалент)
- Заготовка OBS Scene Collection / template export (README + пример JSON/файл)
- Расширить `scripts/verify.ps1` под новые тесты
- Owner smoke: Fake match → overlay обновляется; смена сцены из dashboard → Agent (или Fake OBS) применяет

**Вне scope:**

- WebRTC комментаторов / coturn live (→ People Slice)
- Judge mobile UI (API судьи уже есть; UI → People)
- Полный admin wizard турнира / branding upload UX (→ Tournament Slice)
- Twitch delay verification / FFmpeg delay в Agent (ADR-024 v2)
- Живой CS2 VPS как обязательный GATE (достаточно Fake + локальный OBS или Fake OBS)
- Redis / multi-replica API
- BestTvGU

---

## 2. Frozen (не менять без TL)

- **F1:** Dashboard **никогда** не говорит с OBS напрямую — только Platform → Agent (A8)
- **F2:** Overlay = **full snapshot**, не patch; `version` monotonic per match, DB-backed (ADR-032)
- **F3:** Production: **desired** vs **actual** раздельно; Agent = reconciler, не «очередь команд как SoT» (A3, A12)
- **F4:** Watermark STP на overlay **всегда** (продукт / VISION)
- **F5:** Side effects через outbox; API single replica; in-memory WS hub ок (ADR-028, ADR-031, A9)
- **F6:** Domain без OBS WS / ICE типов (A7)
- **F7:** v1 Twitch delay = OBS Stream Delay чек-лист; Agent без FFmpeg delay (ADR-024)
- **F8:** Секреты OBS/Agent только в `.env` / local agent config — не в git, не в `workers/`
- **F9:** Коммиты только @owner
- **F10:** A1–A12 — architectural bugs

---

## 3. To-be / UX

1. Compose Platform up (как Foundation)
2. Создать/взять Fake match со счётом (TZ002 flow)
3. Открыть overlay URL в браузере/OBS Browser Source → виден счёт + watermark
4. Запустить Director Agent (или Fake OBS mode) → статус connected
5. В dashboard режиссёра выбрать сцену (`intro` / `ingame` / …) → actual в OBS (или fake) совпадает с desired
6. Override текста/видимости на overlay → snapshot version++ → клиент обновляется
7. `scripts/verify.ps1` зелёный

---

## 4. Техника

| Слой | Пути |
|------|------|
| Overlay app | `apps/overlay/` (Svelte + Vite) |
| Dashboard | `apps/dashboard/` (SvelteKit или Svelte+Vite — как проще для director route) |
| Director Agent | `apps/director-agent/` (Go) |
| Overlay / production API | `apps/api/` — domain overlay + production; WS presentation |
| Contract | `docs/OVERLAY-CONTRACT.md` или `docs/PRODUCTION-CONTRACT.md` (коротко) |
| OBS template | `apps/director-agent/templates/` или `infra/platform/obs/` |
| Verify | `scripts/verify.ps1` |

**Минимальные API / WS (ориентир):**

- `WS /ws/overlay/{matchId}` → messages `overlay.snapshot`
- `GET /api/v1/matches/{id}/overlay` — текущий snapshot
- `POST /api/v1/matches/{id}/overlay/override` — manual override
- `GET/PATCH /api/v1/matches/{id}/production` — desired scene/stream flags
- `WS` Agent ↔ Platform: session, desired push, actual report
- Dashboard: `/director/[matchId]`

**Сцены (минимум):** `waiting` · `intro` · `teams` · `ingame` · `break` · `winner` (можно сузить до 4 в GATE, остальные stub).

---

## 5. Приёмка

- [x] Контракт overlay + production в репо
- [x] Overlay в Browser Source: snapshot + watermark; reconnect получает полный snapshot
- [x] Смена сцены из dashboard → desired в DB → Agent reconcile → actual (реальный OBS **или** Fake OBS)
- [x] Dashboard не содержит OBS WebSocket client
- [x] Override overlay → version++ и WS push
- [x] Outbox/handlers не роняют API при reconnect Agent
- [x] `verify.ps1` зелёный
- [x] Owner smoke ≤ 15 мин по инструкции в `workers/developer/notes/TZ003-OWNER-SMOKE.md`

---

## 6. Runbook

- `workers/developer/notes/TZ003-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ003-NEW-CHAT.md`
- Промптов: **M = 7** (P7 = GATE)

---

## 7. Паритет

Overlay и dashboard — разные apps; общие типы по возможности через `packages/api-types` (не блокировать GATE генерацией — достаточно ручного контракта).

---

## Контекст

- TZ001: layers, MySQL, outbox, compose, verify
- TZ002: Fake CS2, match/judge API, failure A–E (B = Agent — закрывается здесь)
- [docs/INVARIANTS.md](../docs/INVARIANTS.md) §3.3, §7–8, A8, A12
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) §7, §12, §14
- [docs/LAYERS.md](../docs/LAYERS.md) §5–6
- [docs/DECISIONS.md](../docs/DECISIONS.md) ADR-021, 024, 031, 032
