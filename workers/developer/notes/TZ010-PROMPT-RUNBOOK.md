# TZ010 — PROMPT RUNBOOK · Production Ready

> ТЗ: [tasks/010_PRODUCTION-READY.md](../../../tasks/010_PRODUCTION-READY.md)  
> База: Alpha + TZ009/TZ011 gate_ready; канон комментаторов = WHIP; Fake CI  
> **M = 6** · P6 = GATE · 1 чат = 1 промпт  
> Философия: стабильность и операционка — «второй турнир за часы», не новый эфирный пайплайн

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/6 | RECON gaps + Frozen сверка; TZ010-RECON.md | **done** | 2026-08-12 |
| 2/6 | Production runbook hub (день матча + второй турнир) | **done** | 2026-08-12 |
| 3/6 | Recovery: docs + failure A–E (закрыть B или defer) | **done** | 2026-08-12 |
| 4/6 | Update/deploy: git pull · migrate · compose profiles | **done** | 2026-08-12 |
| 5/6 | Second-tournament checklist/script polish; verify banner prep | **done** | 2026-08-12 |
| 6/6 | verify Fake + TZ010-OWNER-SMOKE + GATE | **done** | 2026-08-12 |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/6 | §0 · §1 · §2 Frozen · §4 · §6 · ROADMAP этап 7 · ALPHA-RUNBOOK · ARCHITECTURE §16 |
| 2/6 | §0 · §3 · docs/alpha/* · ALPHA-LIVE (ссылки) · RECON из P1 |
| 3/6 | §2 F1 · §4 recovery · INVARIANTS / test_failures_a_e · Agent restart |
| 4/6 | §3 · §4 update · scripts/README · infra/platform · mediamtx · .env.example |
| 5/6 | §3 · §5 Secondary · alpha-dry-run · RECON «friction» |
| 6/6 | §5 Приёмка · F1 F5 F6 F7 |

---

## P1/6 — RECON

### Делать

- Пройти существующие доки/скрипты/тесты глазами: что мешает «второй турнир за часы»
- Зафиксировать [TZ010-RECON.md](TZ010-RECON.md):
  - gaps (docs / failure B / update path / дубли alpha)
  - in scope vs out (со ссылкой на ТЗ §1)
  - риск Failure B: fix в P3 **или** явный defer + эскалация TL
- Сверить Frozen F1–F7; не менять без TL

### Не делать

- Писать полный PRODUCTION-RUNBOOK (P2)
- Менять код failure/Agent без нужды
- Twitch GATE / BestTvGU / Prometheus обязательным
- Коммит без @owner

### DoD

- [x] TZ010-RECON.md с приоритетным списком на P2–P5
- [x] Решение по Failure B зафиксировано
- [x] Scope не расползся

### Проверки

- Ревью: каждый gap → номер P или «out»

### После P

- WORKLOG; трекер P1=done; **стоп — P2 в новом чате**

---

## P2/6 — Production runbook hub

### Делать

- Создать hub: `docs/PRODUCTION-RUNBOOK.md` (или имя из RECON) — **один вход** для организатора:
  - день матча (Fake primary; live WHIP/CS2 — ссылки на ALPHA-LIVE / owner smoke)
  - второй турнир: короткие шаги «создать → сетка → старт → staff links»
  - указатели на `docs/alpha/organizer.md`, `director.md`, `judge.md` (не дублировать длинные куски)
- Обновить устаревшие куски alpha docs **минимально** (WHIP-канон уже в director — только дыры из RECON)
- ROADMAP этап 7: ссылка на hub

### Не делать

- Recovery table целиком (P3)
- git pull deploy detail (P4)
- Большой UI dashboard
- Новые фичи матча

### DoD

- [x] Человек без контекста чата находит «что делать в день X» за ≤5 мин по оглавлению
- [x] Нет третьей конкурирующей «правды» без ссылки на hub
- [x] Frozen F3/F4 соблюдены

### Проверки

- Самопроверка clear-writing: убрать жаргон — смысл ясен?

### После P

- WORKLOG; CODE_CHANGE_BOARD; P2=done; новый чат P3

---

## P3/6 — Failure recovery

### Делать

- Человеческая таблица «симптом → действие» в hub или `docs/…-RECOVERY.md` (Platform / Agent / OBS / Bridge / overlay / WHIP waiting)
- Сверка с ARCHITECTURE §16.2–16.3 и INVARIANTS
- `test_failures_a_e.py`: закрыть **Failure B** (Agent restart) минимальным тестом **или** defer по RECON + note в runbook
- Не ломать A/C/D/E

### Не делать

- Новый мониторинг stack
- Рефактор всего Agent
- Требовать живой OBS в CI

### DoD

- [x] Recovery читаем организатору/режиссёру
- [x] pytest failure suite зелёный; B = done или documented defer
- [x] F1: CI без live

### Проверки

- `pytest apps/api/tests/test_failures_a_e.py -q`

### После P

- WORKLOG; CODE_CHANGE_BOARD; P3=done; новый чат P4

---

## P4/6 — Update / deploy path

### Делать

- Документ обновления стенда (секция hub или `docs/UPDATE.md`):
  - `git pull`
  - `alembic upgrade head`
  - compose profiles: default / `webrtc` / `whip`
  - перезапуск API / Agent; MediaMTX если live комментаторы
  - что **не** коммитить (`.env`)
- Минимальный diff в `scripts/README.md`, `infra/platform/README.md`, `infra/mediamtx/README.md` — ссылки на hub
- `.env.example`: только schema-дыры из RECON (без секретов)

### Не делать

- Авто-деплой на VPS без запроса devops/@owner
- Terraform/K8s
- Ломать verify

### DoD

- [x] Путь обновления воспроизводим по доке
- [x] F2: секреты не в git
- [x] Compose profiles упомянуты явно

### Проверки

- `docker compose … config` для нужных profiles (как в verify)

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/6 — Second tournament path + verify prep

### Делать

- Чеклист «второй турнир ≤ N часов» (Fake): конкретно шаги + ссылки на UI/API
- Если RECON указал дешёвый выигрыш — точечный polish `alpha-dry-run.ps1` / маленький helper (**не** обязателен)
- Черновик `TZ010-OWNER-SMOKE.md` (≤30–45 мин): drill recovery + второй Fake-турнир
- Подготовить список артефактов для баннера verify (P6)

### Не делать

- Обязательный live CS2/WHIP/Twitch в Primary smoke
- Большой новый CLI
- P6 verify целиком (оставить прогон на P6)

### DoD

- [x] OWNER-SMOKE draft готов
- [x] Чеклист второго турнира в hub или smoke
- [x] F6 понятен @owner

### Проверки

- Глазами: нет шагов «открой десять разных README без оглавления»

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/6 — verify + OWNER-SMOKE + GATE

### Делать

- `verify.ps1`: баннер TZ010; Fake обязателен; live **не** обязателен
- Довести OWNER-SMOKE; @owner проходит drill
- Статусы: tasks/010 → done (или gate_ready → done после owner); ROADMAP этап 7 note; трекер P6
- CURRENT_TASK / WORKLOG / CODE_CHANGE_BOARD / CURRENT журнал

### Не делать

- Коммит без @owner
- Требовать Twitch/CS2 live для Primary
- Менять Frozen молча

### DoD

- [x] VERIFY OK (Fake)
- [ ] @owner smoke → production ready отмечен
- [x] ТЗ §5 Primary закрыт (кроме owner signature)

### После P

- СТОП; коммиты @owner; TL: Twitch / этап 8 BestTvGU / следующий фокус

---

## Эскалация

| Ситуация | Кому |
|----------|------|
| Failure B требует крупный Agent redesign | TL — defer |
| Нужен обязательный live в GATE | TL (ломает F1) |
| VPS prod update | devops + @owner |
| Diff > ~400 строк за один P | self-review subagent |
| Конфликт «alpha vs production hub» | documentarian / TL |
