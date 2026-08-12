# ТЗ 010 — Production Ready

| Поле | Значение |
|------|----------|
| **Статус** | **gate_ready** (ждёт @owner smoke → done) |
| **Owner** | @owner (приёмка «второй турнир») / @team-lead (постановка) |
| **Исполнитель** | developer (+ @owner smoke P6) |
| **Этап roadmap** | 7 — Production Ready |
| **Предыдущий** | TZ011 OBS WHIP (gate_ready) · TZ009 Live CS2 (gate_ready) · Alpha TZ007 |
| **Следующий** | live Twitch (если open) / BestTvGU API (этап 8) |

**Ранбук:** [TZ010-PROMPT-RUNBOOK.md](../workers/developer/notes/TZ010-PROMPT-RUNBOOK.md)

---

## 0. Цель (для людей)

После одного пробного турнира организатор может **повторить следующий за часы**, а не за дни: понятные инструкции «день матча», что делать при сбое, как обновить стенд без сюрпризов.  
Это не новая фича эфира — **стабильность и операционка**.

---

## 1. Scope

**В scope:**

- Единый **production runbook** для организатора (день матча + второй турнир)
- Runbook **восстановления** по сценариям сбоев (Platform / Agent / OBS / Bridge / overlay) — человек + сверка с кодом
- Документ **обновления стенда**: `git pull`, migrate, compose profiles, Agent, MediaMTX/WHIP, `.env` без секретов в git
- Закрыть явные дыры в тестах failure A–E, где дёшево (в т.ч. Failure B Agent restart, если ещё skip)
- Чеклист / smoke «второй турнир быстрее первого» (Fake primary; live-треки — опционально по статусу ALPHA-LIVE)
- `verify.ps1` остаётся зелёным (Fake); баннер TZ010
- Owner smoke → трек/заметка `production_ready=done` (или эквивалент в ROADMAP / ALPHA)

**Вне scope:**

- Новые продуктовые фичи эфира (Twitch GATE, новый SFU, BestTvGU API)
- Kubernetes / multi-tenant SaaS
- Другие игры
- Обязательный Prometheus/Grafana (можно secondary / note)
- Вырезание Fake/Pion; обязательный живой CS2 DS / OBS WHIP для CI
- Полный редизайн dashboard

**Уже есть (переиспользовать):**

- `docs/alpha/*`, ALPHA-RUNBOOK, ALPHA-LIVE-TRACKS
- Failure A–E (`test_failures_a_e.py`), INVARIANTS recovery, ARCHITECTURE §16
- `scripts/verify.ps1`, `alpha-dry-run.ps1`, `dev-remote.ps1`, `live-cs2-local.ps1`
- Match health, audit log, WHIP/WHEP (TZ011), Live CS2 Local (TZ009)

---

## 2. Frozen (не менять без TL)

- **F1:** Primary CI GATE = **Fake** path; live OBS/CS2/Twitch **не** обязательны в `verify.ps1`
- **F2:** Секреты только в `.env` / runtime — не в git, WORKLOG, чат
- **F3:** Минимальный diff; не переписывать архитектуру «заодно»
- **F4:** Канон комментаторов = OBS WHIP (TZ011); `--live-webrtc` остаётся deprecated
- **F5:** A1–A12; коммиты только @owner
- **F6:** «Второй турнир за часы» измеряется чеклистом @owner (Fake достаточно для Primary; live — Secondary)
- **F7:** Не объявлять Alpha «production ready» без прохождения §5

---

## 3. To-be / UX (для людей)

1. Организатор открывает **один** production runbook и проходит день матча без охоты по десяти файлам.
2. При сбое — таблица «симптом → действие» (перезапуск Agent, refresh overlay, reconcile…).
3. Обновление: короткие шаги `git pull` → migrate → поднять нужные profiles → проверить `/ready`.
4. Второй турнир: создать/опубликовать → сетка → старт → ссылки staff — по часам, не с нуля искать доки.
5. Developer: `verify.ps1` зелёный; owner отмечает smoke.

---

## 4. Техника

| Слой | Пути / артефакты |
|------|------------------|
| Hub runbook | `docs/PRODUCTION-RUNBOOK.md` (или эквивалент; ссылки на alpha/*) |
| Recovery | docs + `apps/api/tests/test_failures_a_e.py` (+ Agent, если B) |
| Update | `docs/` + `scripts/README.md` / infra README |
| Smoke | `workers/developer/notes/TZ010-OWNER-SMOKE.md` |
| Recon | `workers/developer/notes/TZ010-RECON.md` (P1) |
| Verify | `scripts/verify.ps1` баннер TZ010 |
| Статус | ROADMAP этап 7 · опционально ALPHA / PROJECT note |

```text
Organizer ──runbook──► day-of + 2nd tournament
Ops         ──recovery──► restart / reconcile / refresh
DevOps-ish  ──update──► git pull + migrate + compose
CI          ──verify Fake──► VERIFY OK (no live required)
```

---

## 5. Приёмка

### Primary GATE

- [x] RECON: список дыр и решение «в scope / out»
- [x] Production runbook (день матча + второй турнир) — читаемый человеком
- [x] Recovery runbook + failure tests без регрессии (A–E; B закрыт или явно documented defer с TL)
- [x] Update/deploy documented (`git pull` path)
- [x] `verify.ps1` → VERIFY OK (Fake)
- [ ] @owner smoke → production ready отмечен (второй турнир / drill по чеклисту)

### Secondary

- [ ] Health/dashboard одна строка «что смотреть в день матча»
- [ ] Заметка Prometheus «не в этой волне» или минимальный stub
- [ ] Скрипт-хелпер второго турнира (если дешевле чеклиста — не обязателен)

---

## 6. Риски

| Риск | Митигация |
|------|-----------|
| Расползание в фичи | Frozen F3; out of scope жёстко |
| Live-треки ещё gate_ready | Primary на Fake; live — Secondary / ссылки ALPHA-LIVE |
| Дублирование alpha docs | Hub + ссылки, не копипаст трёх версий правды |
| Failure B дорогой | P3: минимальный тест или явный defer в RECON + TL |

---

*ТЗ 010 · StudentTournamentKit · этап 7*
