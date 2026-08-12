# Tournament Alpha — runbook

> Первый внутренний полный турнир end-to-end.  
> ТЗ: [tasks/007_TOURNAMENT-ALPHA.md](../tasks/007_TOURNAMENT-ALPHA.md) · этап roadmap 6.  
> Приёмка владельца: чеклист ниже · подробный smoke — `workers/developer/notes/TZ007-OWNER-SMOKE.md` (после P6).  
> **Повторный день / второй турнир:** единый вход — [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md) (этап 7).

---

## Цель Alpha

Провести **один полный дистанционный турнир на стенде Fake**: организатор создаёт кубок и сетку, режиссёр ведёт «эфир», судья работает с телефона, на экране видны overlay / состояние эфира / журнал действий. Live CS2, живой OBS, Twitch и WebRTC — **не обязательны** для приёмки.

После дня: владелец проходит чеклист и пишет post-mortem ([шаблон](alpha/POST-MORTEM-TEMPLATE.md)). Live optional: [ALPHA-LIVE-TRACKS.md](ALPHA-LIVE-TRACKS.md).

---

## Границы (не расширять без тимлида)

| Правило | Смысл |
|---------|--------|
| **4 команды**, сетка на выбывание | Минимум Alpha; 8+ команд — позже |
| **Fake — основной путь** | Матч стартует без игрового сервера; Agent с `--fake-obs` |
| Live — по желанию | Локальный CS2, реальный OBS, Twitch, WebRTC = отдельные треки, по умолчанию **blocked** |
| Код только под дыры репетиции | Не новый продуктовый срез |

---

## Роли

| Кто | Где работает | Что делает в день Alpha |
|-----|--------------|-------------------------|
| **Организатор** | Админка `/admin` | Логин → турнир → 4 команды → сетка → старт матча → ссылки staff |
| **Режиссёр** | `/director/{матч}` + Agent | Сцены, чек-лист задержки, смотрит «Состояние эфира» |
| **Судья** | Телефон, invite-ссылка | Запрос разбора → продолжить или тех. поражение |
| **Комментатор** (опционально) | `/watch` | Смотрит картинку (mock / fake WebRTC достаточно) |
| **Владелец** | Этот runbook | Чеклист приёмки + post-mortem |

Секреты и пароли — только в `.env` на машине; не в чат и не в git.

---

## Порядок дня (репетиция Fake)

Типичная последовательность. Детальные клики — в памятках ниже и в smoke-срезах.

| Роль | Памятка |
|------|---------|
| Организатор | [docs/alpha/organizer.md](alpha/organizer.md) |
| Режиссёр | [docs/alpha/director.md](alpha/director.md) |
| Судья | [docs/alpha/judge.md](alpha/judge.md) |

1. **Поднять стенд** — MySQL (compose), API с миграциями, dashboard / overlay / judge (dev или сборка).
2. **Организатор** — войти в админку → создать турнир → опубликовать → добавить **4 команды** → создать сетку → заполнить слоты → **Старт (Fake)** у первого матча → скопировать ссылки режиссёра и судьи. → [organizer.md](alpha/organizer.md)
3. **Режиссёр** — открыть панель по ссылке → запустить Agent с `--fake-obs` → дождаться «всё в порядке» в состоянии эфира → пройти чек-лист задержки (на Fake достаточно прочитать пункты) → переключить сцены. → [director.md](alpha/director.md)
4. **Судья** — открыть invite → запросить разбор → завершить (продолжить или тех. поражение). → [judge.md](alpha/judge.md)
5. **Overlay** — открыть `/overlay/{матч}`: сцены и брендинг читаемы; watermark STK на месте.
6. **Проверки эфира** — health (платформа / агент / OBS / overlay) и журнал действий отражают смену сцен и действия судьи.
7. **Владелец** — пройти [чеклист приёмки](#чеклист-приёмки-владельца-fake-e2e) → кратко зафиксировать итог (полный smoke TZ007 — в P6).

Автоматизация проверки стенда: [`scripts/alpha-dry-run.ps1`](../scripts/alpha-dry-run.ps1) (verify + этот порядок руками). Детали флагов: [`scripts/README.md`](../scripts/README.md) § alpha-dry-run.

---

## Срезы, на которых держится Alpha

Каждый срез уже принят на Fake. Перед днём Alpha можно освежить нужный кусок:

| Срез | Что закрывает | Owner smoke |
|------|---------------|-------------|
| TZ002 Game | Fake-матч, счёт, пауза судьи на buy | [TZ002-OWNER-SMOKE.md](../workers/developer/notes/TZ002-OWNER-SMOKE.md) |
| TZ003 Production | Overlay + Agent + Fake OBS, сцены | [TZ003-OWNER-SMOKE.md](../workers/developer/notes/TZ003-OWNER-SMOKE.md) |
| TZ004 People | Invite судьи/комментатора, `/watch`, judge UI | [TZ004-OWNER-SMOKE.md](../workers/developer/notes/TZ004-OWNER-SMOKE.md) |
| TZ005 Tournament | Админка, 4 команды, сетка, staff-ссылки, брендинг | [TZ005-OWNER-SMOKE.md](../workers/developer/notes/TZ005-OWNER-SMOKE.md) |
| TZ006 Broadcast | Задержка, 6 сцен overlay, health, журнал | [TZ006-OWNER-SMOKE.md](../workers/developer/notes/TZ006-OWNER-SMOKE.md) |

Контракты: [OVERLAY-CONTRACT.md](OVERLAY-CONTRACT.md) · [BROADCAST-DELAY.md](BROADCAST-DELAY.md) · [BROADCAST-HEALTH.md](BROADCAST-HEALTH.md).

Live-треки: `live_obs` = **done**; `live_webrtc` = **done** (deprecated); `live_whip` / `live_cs2_local` / `live_twitch` = **ready** (WHIP — канон комментаторов). Шаги: [ALPHA-LIVE-TRACKS.md](ALPHA-LIVE-TRACKS.md).

---

## Чеклист приёмки владельца (Fake E2E)

Пройти **по порядку**. Отмечать только то, что видел своими глазами на Fake-стенде.

### A. Организатор (admin)

- [ ] Логин в админку работает
- [ ] Создан и опубликован турнир
- [ ] Добавлены **ровно 4 команды** (игроки по желанию)
- [ ] Сетка на выбывание создана, слоты заполнены, у матчей есть id
- [ ] Первый матч запущен через **Старт (Fake)** (без живого CS2)
- [ ] Скопированы ссылки: режиссёр, судья (комментатор — по желанию)

### B. Матч и режиссёр

- [ ] Панель режиссёра открывается по ссылке
- [ ] Agent с `--fake-obs` подключён; в «Состоянии эфира» агент/OBS не «Нет связи»
- [ ] Чек-лист задержки Twitch виден (на Fake достаточно прочитать; живой Twitch не нужен)
- [ ] Смена сцен (waiting → intro → teams → ingame → break → winner) доходит до overlay

### C. Судья

- [ ] Invite открывается на телефоне или в узком окне браузера
- [ ] Запрос разбора и итог (продолжить **или** тех. поражение) проходят без поломки матча

### D. Overlay / health / audit

- [ ] Overlay показывает актуальные сцену, команды/счёт (и брендинг, если задан); watermark STK на месте
- [ ] Health матча осмысленный (платформа жива; при Fake OBS — эфир не «всё красное»)
- [ ] В журнале действий видны смена сцен и/или действия судьи / старт

### E. Закрытие дня

- [ ] `scripts/verify.ps1` зелёный (или зафиксирован известный блокер)
- [ ] Primary путь = **Fake**; live не требовался для этой приёмки
- [ ] Post-mortem заполнен хотя бы черновиком ([шаблон](alpha/POST-MORTEM-TEMPLATE.md) / в smoke TZ007)
- [ ] Подпись владельца: дата ______ · результат: принято / не принято · комментарий: ______

Полная пошаговая инструкция ≤40 мин с URL и командами — в `TZ007-OWNER-SMOKE.md` (P6). Этот чеклист — критерий «день Alpha состоялся».

---

## Что появится дальше (не в этом документе целиком)

| Артефакт | Когда |
|----------|--------|
| `scripts/alpha-dry-run.ps1` | **есть** ([README](../scripts/README.md) § alpha-dry-run) |
| Памятки операторов RU (`docs/alpha/…`) | **есть** — [organizer](alpha/organizer.md) · [director](alpha/director.md) · [judge](alpha/judge.md) |
| Live-треки + шаблон post-mortem | **есть** — [ALPHA-LIVE-TRACKS.md](ALPHA-LIVE-TRACKS.md) · [POST-MORTEM-TEMPLATE.md](alpha/POST-MORTEM-TEMPLATE.md) |
| `TZ007-OWNER-SMOKE.md` + GATE | **есть** — [TZ007-OWNER-SMOKE.md](../workers/developer/notes/TZ007-OWNER-SMOKE.md); статус **gate_ready** |
| Production hub (день матча + 2-й турнир) | **есть** — [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md) |

---

## Быстрые URL (локальный dev)

| Куда | Обычно |
|------|--------|
| Админка | `http://127.0.0.1:5174/admin` |
| Режиссёр | `http://127.0.0.1:5174/director/{matchId}` |
| Overlay | `http://127.0.0.1:5173/overlay/{matchId}` |
| Судья | invite из staff-ссылок (порт judge, часто `:5175`) |
| API health | `http://127.0.0.1:8000/health` |

Логин организатора по умолчанию из `.env.example`: `organizer` / пароль из env.
