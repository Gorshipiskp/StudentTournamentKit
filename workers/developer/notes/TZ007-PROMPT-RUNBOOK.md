# TZ007 — PROMPT RUNBOOK · Tournament Alpha

> ТЗ: [tasks/007_TOURNAMENT-ALPHA.md](../../../tasks/007_TOURNAMENT-ALPHA.md)  
> База: TZ001–006 GATE (полный стек на Fake; live optional)  
> **M = 6** · P6 = GATE · 1 чат = 1 промпт  
> Философия: интеграция + runbooks + минимальные фиксы; не новый продуктовый срез

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/6 | ALPHA-RUNBOOK + acceptance checklist | done | 2026-08-12 |
| 2/6 | `alpha-dry-run.ps1` (Fake E2E orchestration) | done | 2026-08-12 |
| 3/6 | Operator guides RU (organizer / director / judge) | done | 2026-08-12 |
| 4/6 | Dry-run gap fixes (blockers only) | done | 2026-08-12 |
| 5/6 | Live tracks doc + post-mortem template | done | 2026-08-12 |
| 6/6 | verify + TZ007-OWNER-SMOKE + GATE (@owner) | done | 2026-08-12 (gate_ready; @owner sign-off pending) |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/6 | §0 · §1 runbook · §2 F1 F5 · §4 |
| 2/6 | §1 dry-run · §3 · TZ002–006 owner smokes |
| 3/6 | §3 UX · §1 operator guides |
| 4/6 | §1 fixes · итоги P2 |
| 5/6 | §1 live tracks · §5 optional · LOCAL-CS2-DS |
| 6/6 | §5 Приёмка · §2 F5 |

---

## P1/6 — ALPHA-RUNBOOK + acceptance checklist

### Делать

- `docs/ALPHA-RUNBOOK.md`: цель Alpha, роли, порядок дня, ссылки на TZ002–006 smokes
- Чеклист приёмки @owner (в smoke doc или отдельный §)
- Frozen scope Alpha (4 teams, Fake primary)
- Обновить ROADMAP этап 6 «in progress»

### Не делать

- Скрипты (P2)
- Код фич
- Live обязательный GATE

### DoD

- [x] Документ понятен нетехнику-организатору
- [x] Чеклист приёмки перечисляет шаги Fake E2E

### После P

- WORKLOG; P1=done; новый чат P2

---

## P2/6 — alpha-dry-run.ps1

### Делать

- `scripts/alpha-dry-run.ps1`: оркестрация Fake E2E
  - Preconditions: `.env`, migrate optional flag
  - Вызов `verify.ps1` или subset
  - Подсказки: API up, Fake CS2, Fake OBS, URLs admin/director/judge/watch
  - Exit code ≠ 0 при провале критичного шага
- `scripts/README.md` § alpha-dry-run
- Не дублировать весь verify — композиция + human steps documented

### Не делать

- Live CS2/Twitch automation
- Новый доменный API

### DoD

- [x] Скрипт запускается на чистой машине с venv/compose по README
- [x] Документированы шаги, которые owner делает руками

### После P

- WORKLOG; P2=done; новый чат P3

---

## P3/6 — Operator guides (RU)

### Делать

- `docs/alpha/organizer.md` — день турнира: login → турнир → матч → ссылки staff
- `docs/alpha/director.md` — OBS template, Agent, сцены, health, delay checklist
- `docs/alpha/judge.md` — invite, review, forfeit (коротко, mobile)
- Ссылки из ALPHA-RUNBOOK; ясный язык (без жаргона)

### Не делать

- Видео/дизайн
- Новый UI

### DoD

- [x] Три гайда ≤ 2 страницы каждый
- [x] Перекрёстные ссылки на существующие README

### После P

- WORKLOG; P3=done; новый чат P4

---

## P4/6 — Dry-run gap fixes

### Делать

- Прогнать `alpha-dry-run.ps1` + записать блокеры
- Исправить **только** блокеры E2E (минимальный diff)
- Обновить dry-run doc если шаги изменились
- Pytest/verify зелёные после фиксов

### Не делать

- Scope creep TZ009 Production Ready
- Рефактор «заодно»

### DoD

- [x] Dry-run проходит без блокеров ИЛИ явный `blocked` с причиной в журнале
- [x] Нет регрессии verify

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/6 — Live tracks + post-mortem

### Делать

- `docs/ALPHA-LIVE-TRACKS.md`: local CS2, real OBS, Twitch, WebRTC — шаги, статус blocked/done
- Ссылка на `infra/game-server/LOCAL-CS2-DS.md`, BROADCAST-DELAY, TZ004 OWNER smoke
- `docs/alpha/POST-MORTEM-TEMPLATE.md` (что сработало / нет / инциденты / next)
- Не требовать live для GATE

### Не делать

- FFmpeg delay
- Новые плагины

### DoD

- [x] Live-треки документированы; default blocked
- [x] Post-mortem шаблон готов

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/6 — verify + OWNER-SMOKE + GATE

### Делать

- `workers/developer/notes/TZ007-OWNER-SMOKE.md` (≤40 мин Fake + чеклист приёмки)
- `verify.ps1` — строка/шаг TZ007 если нужно
- Пройти primary GATE §5; отметить ТЗ
- Трекер all done; CURRENT; WORKLOG; CODE_CHANGE_BOARD; ROADMAP этап 6
- Статусы live_* = blocked unless owner отметил

### Не делать

- Объявлять Alpha «production ready» (это TZ008)

### DoD

- [x] verify + alpha-dry-run OK
- [x] OWNER-SMOKE написан; GATE = **gate_ready** (close после @owner sign-off)

### После P

- Следующая волна: TZ008 Live WebRTC → TZ009 Production Ready (после подписи @owner Alpha)

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/6 из TZ007-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
