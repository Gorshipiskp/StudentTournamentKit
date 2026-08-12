# ТЗ 007 — Tournament Alpha (первый полный турнир)

| Поле | Значение |
|------|----------|
| **Статус** | gate_ready (Fake verify+dry-run OK; @owner smoke + post-mortem pending) |
| **Owner** | @owner (приёмка) / @team-lead (постановка) |
| **Исполнитель** | developer (+ owner на репетиции) |
| **Этап roadmap** | 6 — Tournament Alpha |
| **Предыдущий** | TZ006 Broadcast Slice (GATE closed; `live_twitch=blocked`) |
| **Следующий** | TZ008 Live WebRTC → TZ009 Production Ready |

---

## 0. Цель (для людей)

Провести **первый внутренний дистанционный турнир** end-to-end: организатор создаёт кубок, сетка, матчи, режиссёр ведёт эфир, судья с телефона, комментатор (fake/live optional), результаты зафиксированы. Владелец принимает по чеклисту и пишет post-mortem.

Минимум **4 команды** (single-elim). Код — только то, что закрывает дыры репетиции; не новая платформа.

---

## 1. Scope

**В scope:**

- Единый **Alpha runbook** + чеклист приёмки @owner
- Скрипт **`alpha-dry-run.ps1`**: полный Fake-путь (admin → bracket → match → Fake CS2 → director/Fake OBS → judge → overlay/health/audit)
- **Операторские памятки** RU: организатор, режиссёр, судья (день турнира)
- **Live-треки** (док + статус): локальный CS2 DS, реальный OBS, Twitch delay, WebRTC — optional, не блокер primary GATE
- Минимальные **фиксы** по итогам dry-run (только блокеры E2E)
- Post-mortem шаблон
- `verify.ps1` + `TZ007-OWNER-SMOKE.md` (≤ 40 мин dry-run; live — отдельный optional блок)
- Primary GATE на **Fake** (как TZ001–006)

**Вне scope:**

- Новые фичи продукта (новые срезы roadmap 7+)
- BestTvGU API
- Multi-tenant SaaS
- Обязательный live Twitch / live CS2 VPS / live WebRTC для GATE
- Автоматизация OBS delay
- 8+ команд bracket polish

**Уже есть:**

- TZ001–006 vertical slices GATE
- `LOCAL-CS2-DS.md`, STK.Bridge health, MatchZy на машине @owner
- Owner smokes TZ002–006 (переиспользовать)

---

## 2. Frozen (не менять без TL)

- **F1:** Primary GATE = **Fake** E2E; live — optional tracks
- **F2:** Single-elim 4 команды — минимум Alpha
- **F3:** OBS Stream Delay v1 (ADR-024); не FFmpeg
- **F4:** Judge mobile + director + admin — без регрессии TZ004–006
- **F5:** Post-mortem обязателен для GATE @owner
- **F6:** Секреты не в git; коммиты только @owner
- **F7:** A1–A12

---

## 3. To-be / UX (день Alpha)

1. Организатор: login → турнир → 4 команды → сетка → publish → старт матча(ей)
2. Режиссёр: director → сцены → health зелёный → delay checklist
3. Судья: invite → review flow на Fake-матче
4. Комментатор: `/watch` (mock/fake-webrtc ok)
5. Overlay + audit + health на протяжении матча
6. @owner: чеклист приёмки + post-mortem

---

## 4. Техника

| Артефакт | Путь |
|----------|------|
| Alpha runbook | `docs/ALPHA-RUNBOOK.md` |
| Dry-run | `scripts/alpha-dry-run.ps1` |
| Operator guides | `docs/alpha/organizer.md`, `director.md`, `judge.md` |
| Live tracks | `docs/ALPHA-LIVE-TRACKS.md` |
| Post-mortem | `docs/alpha/POST-MORTEM-TEMPLATE.md` |
| Owner smoke | `workers/developer/notes/TZ007-OWNER-SMOKE.md` |

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] `alpha-dry-run.ps1` зелёный (Fake E2E) — 2026-08-12 developer
- [x] `verify.ps1` зелёный — **VERIFY OK — TZ007**
- [x] Operator guides + ALPHA-RUNBOOK в репо
- [ ] @owner прошёл `TZ007-OWNER-SMOKE.md` (Fake)
- [ ] Post-mortem заполнен (хотя бы draft)
- [ ] Чеклист приёмки подписан @owner в smoke doc

### Optional live tracks

- [ ] Локальный CS2 DS + Bridge webhook → Platform (`live_cs2_local`) — **ready**
- [x] Реальный OBS (не Fake) на матче (`live_obs`) — **done** (2026-08-12)
- [ ] Twitch с Stream Delay (`live_twitch`) — **ready**
- [x] Agent WebRTC Virtual Cam (`live_webrtc`) — **done** (TZ008, 2026-08-12)

Статусы live: [ALPHA-LIVE-TRACKS.md](../docs/ALPHA-LIVE-TRACKS.md) (`ready` = можно проходить; `done` = пройдено).

> Full GATE close = после подписи @owner в `TZ007-OWNER-SMOKE.md` + черновик post-mortem. До того: **gate_ready**, не production.

---

## 6. Runbook

- `workers/developer/notes/TZ007-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ007-NEW-CHAT.md`
- Промптов: **M = 6** (P6 = GATE)

---

## 7. Паритет

Репетиция на Fake; live — по готовности инфраструктуры владельца.
