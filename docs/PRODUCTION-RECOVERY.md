# Production recovery — симптом → действие

> Кому: режиссёр и владелец стенда в день матча.  
> Вход: [PRODUCTION-RUNBOOK.md](PRODUCTION-RUNBOOK.md).  
> Система (не человек): [ARCHITECTURE §16](ARCHITECTURE.md#16-отказоустойчивость-и-recovery) · [INVARIANTS](INVARIANTS.md) A12 / § recovery.

**Правило:** сначала проверь «Состояние эфира» / health матча и `/health` API — потом перезапуски.

Секреты не копируй в чат. Токены Agent / WHIP — только из `.env` или API на своей машине.

---

## Быстрая таблица

| Симптом | Что сделать | Кто |
|---------|-------------|-----|
| Админка / API не открываются | Проверь `http://127.0.0.1:8000/health` и `/ready`. Подними MySQL + API (compose / процесс). Обнови страницу. | Владелец |
| Overlay «замёрз» или старая сцена | Обнови Browser Source в OBS **или** открой `/overlay/{матч}` и обнови вкладку. Сверь, что Platform жив. | Режиссёр |
| Агент «Нет связи» | Перезапусти Agent с тем же `match id` и `STK_AGENT_TOKEN`. После старта он сам подтянет **желаемую** сцену (не историю команд). | Режиссёр |
| OBS упал / чёрный экран сцен | Открой OBS заново; убедись, что имена сцен совпадают с шаблоном. Agent переподключится и выровняет сцену. | Режиссёр |
| Сцена в панели есть, в OBS нет | Имена сцен **один в один** (регистр). На Fake — флаг `--fake-obs`. | Режиссёр |
| Счёт / фаза «врёт» после сбоя сервера | Дождись heartbeat Bridge или нажми reconcile / refresh health (если есть в UI). Система чинит через snapshot, не руками в БД. | Организатор / владелец |
| Игровой сервер молчит (live CS2) | Проверь CS2 DS + STK.Bridge; connect игроков; смотри [LOCAL-CS2-DS](../infra/game-server/LOCAL-CS2-DS.md). На Fake GATE это не нужно. | Владелец |
| Судья: ссылка пустая / «протухла» | Организатор выдаёт **новую** invite из «Ссылки для команды». | Организатор |
| Судья нажал итог, матч странный | Не дублируй resolve; смотри журнал действий. Гонка с раундом закрыта на сервере (тест E). | Судья / организатор |
| `/watch`: «режиссёр ещё не начал эфир (WHIP)» | В OBS: **Start Streaming** (Service WHIP). MediaMTX profile `whip`. Path `stk/<matchId>`. | Режиссёр |
| WHIP 401 / 403 | Заново `whip-publish` → обнови Bearer в OBS. | Организатор / режиссёр |
| `/watch` чёрный при живом WHIP | Проверь MediaMTX контейнер; ICE / firewall; на репетиции используй `?media=fake`. | Владелец |
| Не уверен в стенде | `.\scripts\verify.ps1` или `.\scripts\alpha-dry-run.ps1` | Владелец |

Детали WHIP и Agent: [alpha/director.md](alpha/director.md).

---

## Сценарии A–E (что система уже умеет)

Человеку не нужно «чинить код» — достаточно знать, что покрыто тестами.

| Код | Сценарий | Поведение | Где проверено |
|-----|----------|-----------|----------------|
| **A** | Platform перезапустился во время матча | Snapshot с игрового адаптера чинит счёт / sequence | `test_failures_a_e.py` · A |
| **B** | Agent перезапустился во время эфира | Берёт **desired** production, не replay команд (A12) | Go `TestRestartAppliesDesiredNotHistory` + pointer в `test_failures_a_e.py` · B |
| **C** | Дубль webhook | Один `event_id` → второй раз no-op | `test_failures_a_e.py` · C |
| **D** | События не по порядку | Sequence gap → snapshot / reconcile | `test_failures_a_e.py` · D |
| **E** | Судья и раунд одновременно | Версия / FSM на сервере; stale reject | `test_failures_a_e.py` · E |

**Failure B:** закрыт в коде Agent (TZ003). Новых тестов Python на логику B в этой волне **не** требуется. CI primary = Fake (`go test` Agent + pointer pytest); живой OBS в CI не нужен.

---

## Что делает система сама (кратко)

| Сбой | Авто |
|------|------|
| Перезапуск Platform | Активные матчи → snapshot CS2 → overlay → Agents получают desired |
| Перезапуск Agent | Auth → desired → сверка OBS → report actual |
| Перезапуск Bridge | Heartbeat → snapshot → сравнение sequence → события снова |
| Обрыв overlay WS | Клиент reconnect → `overlay.snapshot` |

Полная матрица деградации: [ARCHITECTURE §16.1](ARCHITECTURE.md#161-матрица-деградации).

---

## Чего не делать

- Не править счёт руками в MySQL «на живом».
- Не включать legacy `--live-webrtc` / Virtual Cam как «лечение» WHIP — канон = OBS WHIP.
- Не требовать Prometheus / новый мониторинг в день матча — достаточно health в панели режиссёра.
