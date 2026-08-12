# TZ010 — Owner smoke (≤ 45 мин)

> **Production Ready** — второй турнир за часы + drill recovery.  
> Hub: [PRODUCTION-RUNBOOK.md](../../../docs/PRODUCTION-RUNBOOK.md)  
> Recovery: [PRODUCTION-RECOVERY.md](../../../docs/PRODUCTION-RECOVERY.md)  
> Update: [UPDATE.md](../../../docs/UPDATE.md)  
> ТЗ: [tasks/010_PRODUCTION-READY.md](../../../tasks/010_PRODUCTION-READY.md)

| Поле | Значение |
|------|----------|
| **Primary** | **Fake** — без live CS2 / OBS WHIP / Twitch |
| **CI Fake** | ✅ `verify.ps1` → VERIFY OK (TZ010) |
| **Статус Primary GATE** | ⏳ **gate_ready** — ждёт проход @owner ниже |
| **`production_ready=done`** | только после подписи @owner ниже |

Secondary (не блокер): live WHIP / CS2 — [ALPHA-LIVE-TRACKS](../../../docs/ALPHA-LIVE-TRACKS.md).

---

## Цель smoke

1. Найти день матча с **одного** hub за ≤5 мин.  
2. Пройти **второй** Fake-турнир быстрее «с нуля» (ориентир **≤ 45 мин** wall-clock, если стенд уже поднимался).  
3. Один drill recovery (Agent или overlay) по таблице сбоев.

---

## Подготовка

Стенд уже знаком с Alpha / TZ007. Если нет — сначала [TZ007-OWNER-SMOKE](TZ007-OWNER-SMOKE.md) или `.\scripts\alpha-dry-run.ps1`.

```powershell
cd C:\BestCSTournaments
# авто-чек (Fake; live не нужен):
.\scripts\verify.ps1
# или:
.\scripts\alpha-dry-run.ps1

# стек (если не поднят):
.\scripts\dev-remote.ps1 -MatchId m_prod
# либо ручной API + npm run dev в dashboard / overlay / judge
```

Логин: `organizer` / пароль из `.env`. Секреты не в чат.

**В день матча смотри health здесь:** панель режиссёра → «Состояние эфира» + `GET /api/v1/matches/{id}/health` ([BROADCAST-HEALTH](../../../docs/BROADCAST-HEALTH.md)).

---

## A. Навигация (≤ 5 мин)

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | Открой [PRODUCTION-RUNBOOK](../../../docs/PRODUCTION-RUNBOOK.md) | Оглавление: день матча, 2-й турнир, recovery, update |
| 2 | По оглавлению найди [PRODUCTION-RECOVERY](../../../docs/PRODUCTION-RECOVERY.md) | Таблица симптом → действие без охоты по ARCHITECTURE |

- [ ] Нашёл «что делать сегодня» без десяти README

---

## B. Второй Fake-турнир (≤ 30 мин)

Не править старый сыгранный кубок «вслепую» — **новый** турнир.

| # | Действие | Ожидание | Ссылка |
|---|----------|----------|--------|
| 1 | `/health` → 200 | API жив | |
| 2 | `/admin` → **создать** турнир → опубликовать | Не черновик | [organizer](../../../docs/alpha/organizer.md) |
| 3 | **4 команды** → **создать сетку** → слоты | Есть матчи | organizer |
| 4 | У первого матча **Старт (Fake)** | Матч live; новый `match_id` | |
| 5 | **Ссылки для команды** → режиссёр + судья | Новые URL (старые invite не использовать) | |
| 6 | Agent `--fake-obs` на **новый** match id / токен | «Состояние эфира» не «Нет связи» | [director](../../../docs/alpha/director.md) |
| 7 | Смена 2–3 сцен (например waiting → intro → ingame) | Overlay обновляется | |
| 8 | Судья: invite → разбор → продолжить **или** тех. поражение | Журнал/матч целы | [judge](../../../docs/alpha/judge.md) |

- [ ] Второй кубок прошёл без «искать Alpha с нуля»
- [ ] Время от шага 2 до 8: ______ мин (цель ≤ 30 при живом стенде)

---

## C. Drill recovery (≤ 10 мин)

Выбери **один** сценарий из [PRODUCTION-RECOVERY](../../../docs/PRODUCTION-RECOVERY.md):

| Вариант | Действие | Ожидание |
|---------|----------|----------|
| **C1 Agent** | Останови Agent → снова `go run` / exe с тем же match + токеном | Сцена восстанавливается из **desired** (не руками в OBS) |
| **C2 Overlay** | «Заморозь» вкладку overlay → refresh Browser Source или F5 на `/overlay/{id}` | Актуальная сцена |

- [ ] Drill C1 или C2 пройден; симптом закрыт по таблице

---

## D. Закрытие (подпись @owner)

- [ ] Primary = **Fake**; live CS2/WHIP/Twitch **не** требовались
- [ ] Hub + recovery + update открывались из PRODUCTION-RUNBOOK
- [ ] `verify.ps1` зелёный (developer P6 или владелец)
- [ ] Второй турнир ощущается «за часы», не «за дни документов»

| Поле | Значение |
|------|----------|
| Дата | |
| Результат | принято / не принято |
| Время 2-го турнира (мин) | |
| Комментарий | |

После приёмки отметь:
- `tasks/010_PRODUCTION-READY.md` → **done**
- ROADMAP этап 7 → production ready
- этот файл: статус → **done** / `production_ready=done`

---

## Артефакты (проверяет `verify.ps1`)

| Артефакт | Путь |
|----------|------|
| Hub | `docs/PRODUCTION-RUNBOOK.md` |
| Recovery | `docs/PRODUCTION-RECOVERY.md` |
| Update | `docs/UPDATE.md` |
| Owner smoke | `workers/developer/notes/TZ010-OWNER-SMOKE.md` |
| RECON | `workers/developer/notes/TZ010-RECON.md` |
| ТЗ | `tasks/010_PRODUCTION-READY.md` |

Live MediaMTX / OBS **не** в Fake GATE.
