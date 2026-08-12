# ТЗ 005 — Tournament Slice (организатор + сетка)

| Поле | Значение |
|------|----------|
| **Статус** | **done** (GATE 2026-08-12; Fake match; live_cs2/live_webrtc=blocked) |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer |
| **Этап roadmap** | 4 — Tournament Slice |
| **Предыдущий** | TZ004 People Slice (GATE closed; `live_webrtc=blocked`) |
| **Следующий** | TZ006 Broadcast Slice |

---

## 0. Цель (для людей)

Нетехнический организатор в браузере создаёт турнир, добавляет команды, собирает сетку на выбывание, запускает матч и раздаёт ссылки режиссёру, судье и комментаторам — **без правки конфигов и без SSH**.

На одном инстансе можно вести несколько турниров параллельно. Логотип и цвета турнира видны в эфире (overlay).

---

## 1. Scope

**В scope:**

- Организаторский вход на инстанс (простой login → session/JWT; instance-per-organizer)
- Турниры: draft → published → completed; список, создание, редактирование имени/формата, publish
- Команды и игроки (nickname; steam_id опционально)
- Сетка **single elimination**, ручная (расстановка команд по узлам); узлы → матчи
- Создание/старт матча из сетки (переиспользовать Fake CS2 / существующий match lifecycle)
- Branding: logo + colors (BLOB/limits по ARCHITECTURE); overlay показывает branding
- Admin UI в `apps/dashboard/`: `/admin` wizard (турнир → команды → сетка → инвайты)
- Инвайты director / judge / commentator из UI (API TZ004)
- Multi-tournament: ≥2 турнира на одном инстансе без коллизий
- Расширить `scripts/verify.ps1` + Owner smoke ≤ 25 мин
- Primary GATE на Fake match (без live CS2 / live WebRTC)

**Вне scope:**

- Автосейв / Swiss / double elim / round robin
- BestTvGU виджеты и публичный read API (этап 8)
- OBS Stream Delay / Broadcast polish (→ TZ006)
- Полноценный multi-user RBAC (один organizer на инстанс достаточно)
- Live CS2 VPS как обязательный GATE
- SFU, аудио WebRTC, SaaS multi-tenant

**Уже есть (переиспользовать):**

- `tournaments` + `CreateTournamentDraft` / foundation probe
- Match create/start, Fake CS2, judge, overlay, production, invites (TZ002–004)
- `apps/dashboard/` DirectorPage — не ломать; добавить `/admin`

---

## 2. Frozen (не менять без TL)

- **F1:** Instance-per-organizer; не multi-tenant SaaS (VISION / ARCHITECTURE)
- **F2:** Один турнир = CS2 only; формат матчей задаётся на турнире
- **F3:** Bracket: single elim + **ручная** расстановка в v1
- **F4:** Branding в MySQL BLOB; logo ≤2MB, bg ≤5MB (ARCHITECTURE §8.2)
- **F5:** Invite tokens: hash, scope, revoke (TZ004 / F4 People)
- **F6:** Match lifecycle и CS2 adapter — не переписывать; только связать с bracket
- **F7:** Overlay = full snapshot; branding — поля snapshot, не отдельный хак (A12)
- **F8:** Секреты в `.env`; коммиты только @owner
- **F9:** A1–A12; outbox для значимых tournament events где уместно

---

## 3. To-be / UX

1. Организатор логинится → видит список турниров → «Создать турнир»
2. Заполняет название, число команд (степень 2: 4/8/16), delay hint (число, без automation)
3. Добавляет команды и игроков
4. На экране сетки ставит команды в слоты; система создаёт узлы/матчи
5. Publish → выбирает матч → «Старт» (Fake) → копирует ссылки: режиссёр, судья, комментатор
6. Второй турнир создаётся рядом и не мешает первому
7. Overlay матча показывает лого/цвета турнира

---

## 4. Техника

| Слой | Пути |
|------|------|
| Auth | `apps/api` `/api/v1/auth/*`; env bootstrap secret/password |
| Domain | `domain/tournament/`, `domain/bracket/` (или пакет в tournament) |
| HTTP | `/tournaments`, `/tournaments/{id}/teams`, `/bracket`, расширить `/invites` |
| Persistence | Alembic: name/format/settings, teams, players, bracket_nodes, branding |
| Dashboard | `apps/dashboard` routes `/admin`, `/admin/tournaments/[id]/…` |
| Overlay | snapshot + branding merge |
| Docs | короткий `docs/TOURNAMENT-ADMIN.md` или § в README dashboard |

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] Login организатора; без токена admin API 401
- [x] Создать 2 турнира; у каждого свои команды
- [x] Single-elim сетка 4 команды; матчи привязаны к узлам
- [x] Publish + старт матча (Fake) из admin
- [x] Из UI получить invite-ссылки judge + commentator (+ director/dashboard path)
- [x] Branding виден в overlay snapshot / UI
- [x] `verify.ps1` зелёный
- [x] Owner smoke ≤ 25 мин (инструкция: `workers/developer/notes/TZ005-OWNER-SMOKE.md`)

### Optional

- [ ] 8-team bracket
- [ ] bg image на overlay
- [ ] live CS2 с турнирного матча
- [x] Статус: `live_cs2=blocked` · `live_webrtc=blocked` (наследует TZ004)

---

## 6. Runbook

- `workers/developer/notes/TZ005-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ005-NEW-CHAT.md`
- Промптов: **M = 7** (P7 = GATE)

---

## 7. Паритет

Admin — desktop web. Mobile judge / watch — без регрессии TZ004.
