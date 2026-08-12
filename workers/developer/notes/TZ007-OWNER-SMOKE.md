# TZ007 — Owner smoke (≤ 40 мин)

> Tournament Alpha GATE. **Fake E2E** — без live CS2 / Twitch / WebRTC / реального OBS.  
> Runbook: [docs/ALPHA-RUNBOOK.md](../../../docs/ALPHA-RUNBOOK.md)  
> Памятки: [organizer](../../../docs/alpha/organizer.md) · [director](../../../docs/alpha/director.md) · [judge](../../../docs/alpha/judge.md)  
> Live optional: [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md)  
> Post-mortem: [POST-MORTEM-TEMPLATE.md](../../../docs/alpha/POST-MORTEM-TEMPLATE.md)

**Статус Primary GATE:** Fake dry-run + этот smoke + чеклист + черновик post-mortem.  
Live: `live_obs`/`live_webrtc`=**done**; `live_cs2_local`/`live_twitch`=**ready** (не нужны для Fake-приёмки).

---

## Подготовка (один раз)

```powershell
# Быстрый авто-чек стенда (verify внутри):
.\scripts\alpha-dry-run.ps1

# Стек (если API/UI ещё не подняты):
cd infra/platform
docker compose --env-file ../../.env.example up -d mysql

cd ../../apps/api
# env из .env / .env.example (MYSQL :3307, STK_*)
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Другие терминалы:

```powershell
cd apps/dashboard; npm run dev   # :5174 — /admin + /director
cd apps/overlay; npm run dev     # :5173 — overlay + /watch
cd apps/judge; npm run dev       # :5175 — судья
```

Логин админа: `organizer` / пароль из `.env` (пример: `changeme_organizer`).

---

## Шаги Fake E2E (≤ 40 мин)

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `.\scripts\alpha-dry-run.ps1` | **ALPHA DRY-RUN OK** (внутри verify) |
| 2 | `GET http://127.0.0.1:8000/health` | 200 (подними API, если probe был жёлтый) |
| 3 | Админка `/admin` → турнир → **4 команды** → сетка → **Старт (Fake)** | Матч live; есть `match_id` |
| 4 | **Ссылки для команды** → режиссёр + судья (+ watch по желанию) | URL скопированы |
| 5 | `/director/{matchId}` + Agent `--fake-obs` | Health: агент/OBS не «Нет связи»; видны delay checklist и журнал |
| 6 | Сцены waiting → intro → teams → ingame → break → winner | Overlay и журнал обновляются |
| 7 | Судья по invite: запрос проверки → продолжить **или** тех. поражение | UI проходит; в журнале есть след |
| 8 | Overlay `/overlay/{matchId}` | Сцены читаемы; watermark STK |
| 9 | `GET .../health` и `.../audit` | Ответы осмысленные |
| 10 | Чеклист приёмки ниже + черновик post-mortem | Подпись @owner |

Детали кликов: памятки `docs/alpha/*` · smokes TZ005/006 при необходимости.

---

## Чеклист приёмки (подпись @owner)

Сверка с [ALPHA-RUNBOOK.md](../../../docs/ALPHA-RUNBOOK.md) § чеклист.

### A. Организатор
- [ ] Логин, турнир опубликован, 4 команды, сетка, **Старт (Fake)**, staff-ссылки

### B. Режиссёр
- [ ] Панель + Fake OBS; health ок; сцены доходят до overlay; delay checklist виден

### C. Судья
- [ ] Invite на телефоне/узком окне; review → продолжить или тех. поражение

### D. Overlay / health / audit
- [ ] Overlay + watermark; health осмысленный; журнал отражает действия

### E. Закрытие
- [ ] `alpha-dry-run.ps1` / `verify.ps1` зелёные
- [ ] Primary = Fake; live не требовался
- [ ] Post-mortem черновик (копия шаблона или заполненный шаблон)
- [ ] Подпись: дата ______ · **принято / не принято** · комментарий: ______

---

## Optional live (не GATE)

См. [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md). По умолчанию все **blocked**.

---

## Блокеры / notes

| Тема | Статус |
|------|--------|
| Fake E2E (admin → director → judge → overlay) | **достаточен для Primary GATE** |
| Operator guides + ALPHA-RUNBOOK | в репо |
| live_* | **blocked** |
| Production Ready | **TZ009** (не этот smoke) |

**Критерий:** шаги 1–10 без устных пояснений разработчика ≤ 40 мин.
