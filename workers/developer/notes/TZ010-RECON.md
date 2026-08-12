# TZ010-RECON — Production Ready gaps

**Дата:** 2026-08-12  
**Промпт:** 1/6  
**ТЗ:** [tasks/010_PRODUCTION-READY.md](../../../tasks/010_PRODUCTION-READY.md)  
**Цель сверки:** что мешает организатору **повторить турнир за часы** (не новый эфирный пайплайн).

---

## Вердикт

Код Alpha / TZ009 / TZ011 **достаточен** для Fake primary. Дыры — в **операционке и навигации по докам**, не в отсутствии фич.

| Область | Состояние | Куда |
|---------|-----------|------|
| Единый вход «день матча / 2-й турнир» | **Нет** `docs/PRODUCTION-RUNBOOK.md` | **P2** |
| Памятки ролей | Есть `docs/alpha/*` + ALPHA-RUNBOOK (бренд «Alpha») | **P2** (hub + ссылки; минимальный refresh) |
| Recovery человеку | §16.3 короткий; разрозненные таблицы в alpha/director | **P3** |
| Failure A–E тесты | A/C/D/E unit; **B уже покрыт** Go reconciler | **P3** docs only |
| Update `git pull` | Фрагменты в infra/scripts README; нет одного пути | **P4** |
| Второй турнир ≤ часов | Нет явного чеклиста «ещё один кубок» | **P5** |
| verify баннер TZ010 | Сейчас TZ011 | **P6** |
| Prometheus | Отложено TECH-STACK | **out** / Secondary note |
| Twitch / BestTvGU / K8s | — | **out** (§1) |

Frozen F1–F7: **OK**, менять не нужно. Primary CI = Fake; live WHIP/CS2 — ссылки ALPHA-LIVE (gate_ready у owner).

---

## 1. Docs hub (P2)

**Проблема:** организатор прыгает между ALPHA-RUNBOOK, alpha/organizer, TZ007/009/011 OWNER-SMOKE, scripts/README — нет **одного** оглавления «production day».

**Есть:**

- [ALPHA-RUNBOOK.md](../../../docs/ALPHA-RUNBOOK.md) — день репетиции Fake (хорошо, но «Alpha»)
- [organizer.md](../../../docs/alpha/organizer.md) · [director.md](../../../docs/alpha/director.md) · [judge.md](../../../docs/alpha/judge.md)
- Live: [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md) (`live_whip` / `live_cs2_local` gate_ready)

**Дыры:**

| Gap | Деталь | P |
|-----|--------|---|
| G1 | Нет `docs/PRODUCTION-RUNBOOK.md` | P2 |
| G2 | ALPHA-RUNBOOK § срезы: строка live устарела частично (нет `live_whip` в сводке §) | P2 минимально |
| G3 | Нет блока «второй турнир с нуля / с шаблона» в organizer path | P2 оглавление → P5 чеклист |
| G4 | Не плодить 4-ю копию кликов — только hub + ссылки | P2 |

**Имя hub (канон):** `docs/PRODUCTION-RUNBOOK.md` (как в ТЗ §4).

---

## 2. Recovery + Failure B (P3)

**Код Failure B — уже закрыт (не defer):**

- Go: `apps/director-agent/internal/application/reconciler_test.go` → `TestRestartAppliesDesiredNotHistory` (A12)
- Python pointer: `test_failure_B_agent_restart_covered_by_director_agent` в `test_failures_a_e.py`
- ROADMAP этап 3 уже отмечает Failure B через Agent reconciler

**Решение P3:**

| Действие | Делать | Не делать |
|----------|--------|-----------|
| Человеческая таблица симптом→действие | **Да** (hub или `docs/…-RECOVERY` + ссылка) | Redesign Agent |
| Новый pytest логики B | **Нет** (достаточно pointer + `go test` в verify) | Дублировать A12 на Python |
| A/C/D/E | Не трогать без регрессии | — |
| WHIP «режиссёр не стримит» | Одна строка в recovery → director/TZ011 | Новый код MediaMTX |

Эскалация TL **не нужна** по Failure B.

---

## 3. Update / deploy (P4)

**Есть куски:**

- `infra/platform/README.md` — alembic, remote MySQL, ports
- `scripts/README.md` — `dev-remote` + `-Migrate`, `alpha-dry-run -Migrate`
- `infra/mediamtx/README.md` — profile `whip`
- ADR-013 / VISION: обновление через `git pull`

**Дыры:**

| Gap | Деталь | P |
|-----|--------|---|
| G5 | Нет одного чеклиста: `git pull` → migrate → compose profiles → Agent → `/ready` | P4 |
| G6 | Profiles `webrtc` / `whip` не собраны в «когда поднимать» | P4 |
| G7 | `.env.example` — только дыры из практики (если найдутся); иначе skip | P4 optional |

---

## 4. Второй турнир + smoke (P5–P6)

| Gap | Деталь | P |
|-----|--------|---|
| G8 | Нет timed чеклиста «второй Fake-кубок» (создать→сетка→старт→staff) | P5 |
| G9 | Нет `TZ010-OWNER-SMOKE.md` | P5 draft → P6 final |
| G10 | `verify.ps1` баннер TZ011 → TZ010; артефакты PRODUCTION-RUNBOOK | P6 |
| G11 | Health «что смотреть в день матча» — одна строка Secondary | P5 optional |

Live smoke (WHIP/CS2) — **не** Primary (F1/F6); ссылки на TZ011/TZ009 OWNER-SMOKE.

---

## 5. In scope vs out

### In (волна P2–P6)

- Hub PRODUCTION-RUNBOOK  
- Recovery human + сверка §16  
- Update path documented  
- Second-tournament checklist + OWNER-SMOKE  
- verify TZ010 Fake green  

### Out (явно)

- Twitch GATE, BestTvGU API, K8s, SaaS  
- Обязательный Prometheus  
- Вырезание Fake/Pion  
- Обязательный live OBS/CS2 в CI  
- Полный редизайн dashboard  
- Новый Agent encode / MediaMTX фичи  

---

## 6. Приоритет на P2–P5

| # | Gap | P | Effort |
|---|-----|---|--------|
| 1 | G1 hub PRODUCTION-RUNBOOK | P2 | M |
| 2 | G2/G4 alpha ссылки без дублей | P2 | S |
| 3 | Recovery table (+ WHIP waiting) | P3 | M |
| 4 | G5–G6 update path | P4 | M |
| 5 | G8–G9 second tournament + OWNER-SMOKE draft | P5 | M |
| 6 | G10 verify + GATE | P6 | S–M |

---

## 7. Frozen checklist

| ID | Смысл | RECON |
|----|--------|-------|
| F1 | Fake CI primary | OK |
| F2 | Секреты не в git | OK |
| F3 | Минимальный diff | OK — docs-first |
| F4 | WHIP канон | OK — ссылки, не VC |
| F5 | Коммиты @owner | OK |
| F6 | 2-й турнир = owner checklist | OK → P5/P6 |
| F7 | Не звать PR без §5 | OK |

---

## 8. Следующий шаг

**P2** — создать `docs/PRODUCTION-RUNBOOK.md` (оглавление дня матча + второй турнир + указатели на alpha/* и ALPHA-LIVE).

Стоп кода в P1. Коммиты @owner.
