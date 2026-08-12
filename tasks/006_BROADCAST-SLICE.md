# ТЗ 006 — Broadcast Slice (эфир, delay, мониторинг)

| Поле | Значение |
|------|----------|
| **Статус** | done |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer |
| **Этап roadmap** | 5 — Broadcast Slice |
| **Предыдущий** | TZ005 Tournament Slice (GATE closed) |
| **Следующий** | TZ007 Tournament Alpha |

---

## 0. Цель (для людей)

Режиссёр ведёт **полупрофессиональный** эфир: читаемые сцены overlay, чек-лист задержки Twitch (~90–120 с через OBS), панель «всё ли живо» (платформа, агент, OBS, матч), журнал действий по матчу. Публичный Twitch — с задержкой; комментаторы по-прежнему live (TZ004).

---

## 1. Scope

**В scope:**

- **OBS Stream Delay v1** (ADR-024): чек-лист + показ `configured_broadcast_delay_seconds` из турнира на панели режиссёра; без FFmpeg/автоматизации delay в Agent
- **Overlay polish:** сцены `waiting` · `intro` · `teams` · `ingame` · `break` · `winner` — читаемый semi-pro layout, branding турнира (TZ005), watermark STK
- **Health aggregate:** API + UI для матча: Platform, Agent, OBS, overlay revision, game server (Fake/live stub ok)
- **Match audit log:** таблица + запись ключевых действий (judge, director scene, organizer start, system); GET API + UI на director/admin
- Расширить `scripts/verify.ps1` + Owner smoke ≤ 25 мин
- Primary GATE на Fake OBS + Fake match (без обязательного live Twitch)

**Вне scope:**

- FFmpeg delay pipeline в Agent (v2 / ADR-024 fallback)
- Автоматическая настройка OBS Stream Delay из API
- Motion design уровня Faceit
- BestTvGU API
- Live CS2 VPS / live WebRTC как обязательный GATE
- Новые роли RBAC

**Уже есть (переиспользовать):**

- Overlay WS + snapshot (TZ003), director dashboard, Agent/Fake OBS (TZ003)
- `configured_broadcast_delay_seconds` в tournament settings (TZ005)
- OBS template README + `scenes.json` (TZ003 P6)
- Judge/production events, correlation_id, production_sessions (TZ002–003)

---

## 2. Frozen (не менять без TL)

- **F1:** Twitch delay = **OBS Stream Delay** в v1 (ADR-024); Agent не ставит delay
- **F2:** Live WebRTC комментаторам **без** delay (VISION)
- **F3:** Agent — sole OBS authority (A8); dashboard не WebSocket в OBS
- **F4:** Overlay = full snapshot; сцены по именам из `scenes.json`
- **F5:** Watermark STK всегда на overlay
- **F6:** Audit: `correlation_id`, actor, action, match_id (ARCHITECTURE §8)
- **F7:** `configured_broadcast_delay_seconds` — desired/чек-лист, не verified actual OBS в v1
- **F8:** Секреты в `.env`; коммиты только @owner
- **F9:** A1–A12

---

## 3. To-be / UX

1. Организатор задал delay hint при создании турнира (уже есть)
2. Режиссёр на `/director/:matchId` видит: целевую задержку, чек-лист OBS Stream Delay, статусы компонентов
3. Overlay на сценах intro/teams/break/winner выглядит как турнирный эфир (лого/цвета)
4. Действия (смена сцены, judge review, старт матча) попадают в журнал матча
5. Owner smoke: Fake матч + Fake OBS → health зелёный/жёлтый осмысленно; overlay сцены переключаются

---

## 4. Техника

| Слой | Пути |
|------|------|
| Delay UX | `apps/dashboard` director · `docs/BROADCAST-DELAY.md` |
| Overlay | `apps/overlay/` scene components |
| Health | `apps/api` aggregate endpoint + WS optional |
| Audit | `match_audit_log` migration · writers в existing use-cases |
| Docs | `docs/BROADCAST-HEALTH.md` (короткий) |

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] Director UI: delay hint + OBS Stream Delay checklist (RU)
- [x] Overlay: все 6 сцен читаемы + branding + watermark
- [x] `GET /matches/{id}/health` (или `/production/health`) — agent/obs/overlay/game
- [x] Health panel на director dashboard
- [x] Audit: ≥5 типов действий пишутся; UI список по матчу
- [x] `verify.ps1` зелёный
- [x] Owner smoke ≤ 25 мин (Fake OBS)

### Optional

- [ ] Реальный Twitch с delay (owner manual) → `live_twitch=done` · **сейчас `live_twitch=blocked`**
- [ ] Live CS2 в health panel

---

## 6. Runbook

- `workers/developer/notes/TZ006-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ006-NEW-CHAT.md`
- Промптов: **M = 7** (P7 = GATE)

---

## 7. Паритет

Director — desktop. Judge/watch/overlay — без регрессии TZ004.
