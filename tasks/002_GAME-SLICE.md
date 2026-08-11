# ТЗ 002 — Game Slice (матч + CS2-контракт)

| Поле | Значение |
|------|----------|
| **Статус** | approved |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer (+ devops на deploy-cs2) |
| **Этап roadmap** | 1 — Game Slice |
| **Предыдущий** | TZ001 Foundation (done) |
| **Следующий** | TZ003 Production Slice |

---

## 0. Цель (для людей)

Сделать так, чтобы платформа **вела матч**: принимала события с игрового контура, держала статусы матча и судьи, отправляла паузу / продолжение / тех. поражение — сначала на **Fake Game Server** (без твоего VPS), параллельно подготовив **STK.Bridge** и скрипт деплоя CS2 для живой проверки, когда появится сервер.

---

## 1. Scope

**В scope:**

- Контракт CS2 ↔ Platform (события, команды, snapshot, HMAC, sequence, command_id) — документ + код схем
- **Fake Game Server** (`tools/fake-cs2/` или `apps/api` test double + CLI): шлёт webhooks, принимает команды, отдаёт snapshot/ack
- Platform: `POST /api/v1/internal/cs2/events` (HMAC), нормализация, идемпотентность `event_id`, `sequence`
- Domain Match: `MatchStatus` + `ReviewStatus` раздельно; score только из events/snapshot (не «ручной SoT»)
- Commands: `PauseMatch` / `ResumeMatch` / `ForfeitMatch` / `GetSnapshot` + `command_id` + desired/actual
- Judge flow: review_request → pause_pending → (fake) pause на round buy → resolve continue|forfeit
- Game server registry (CRUD stub) + assign server to match
- Reconciliation stub: snapshot vs platform view
- `event_outbox` на match transitions
- `infra/game-server/plugins/STK.Bridge/` — скелет CounterStrikeSharp (C#): config, heartbeat, webhook client, command ack stubs
- `scripts/deploy-cs2.sh` (+ README): SteamCMD/MatchZy/Bridge install steps (исполнение на VPS — когда есть доступ)
- Demo: metadata + **durable copy stub** (локальная папка / volume; не только «файл на ephemeral CS2»)
- Автотесты failure A–E на Fake ([INVARIANTS §16](../docs/INVARIANTS.md))
- `scripts/verify.ps1` расширить под новые тесты

**Вне scope:**

- Overlay / dashboard UI / Director Agent / OBS / WebRTC
- Полная сетка / multi-tournament admin UX
- Живой 5v5 **как обязательный** GATE без VPS (см. §5: primary vs live)
- Переписывание MatchZy
- Redis / multi-replica
- BestTvGU

---

## 2. Frozen (не менять без TL)

- **F1:** MatchZy reuse + **STK.Bridge** thin layer; не fork MatchZy (ADR-010, ADR-023)
- **F2:** Domain без MatchZy/RCON типов — только normalized events/commands (A4, A7)
- **F3:** MatchStatus ≠ ReviewStatus; tech pause не MatchStatus (ADR-026)
- **F4:** Commands idempotent: `command_id` + ack; HTTP 200 ≠ applied (ADR-029, A3, A5)
- **F5:** Events: `event_id` UNIQUE in txn + `sequence`; handlers idempotent (INVARIANTS §6)
- **F6:** Outbox для side effects; single API replica (ADR-028, ADR-031)
- **F7:** CS2→Platform best-effort; pause/unpause/forfeit/load — command path (A1, A11)
- **F8:** Demo durable до teardown CS2 (ADR-034)
- **F9:** Секреты в `.env`; коммиты только @owner
- **F10:** A1–A12 — architectural bugs

---

## 3. To-be / UX (для разработчика и владельца)

**Primary (без VPS):**

1. Поднять Platform (как TZ001)
2. Запустить Fake CS2, привязать к match
3. Сымитировать раунды → score в platform view
4. Судья: review → pause → continue или forfeit через API
5. Failure tests A–E зелёные

**Live (когда есть VPS):**

6. `deploy-cs2.sh` на VPS → Bridge стучится webhooks → тот же API flow

---

## 4. Техника

| Слой | Пути |
|------|------|
| Contract / schemas | `apps/api/app/domain/game_integration/`, `docs/` или `packages/` |
| Fake CS2 | `tools/fake-cs2/` |
| Ingest API | `presentation/http/routers/internal_cs2.py` |
| Match / Judge | `domain/match/`, `application/commands/` |
| Adapter | `infrastructure/adapters/cs2/` |
| Bridge | `infra/game-server/plugins/STK.Bridge/` |
| Deploy | `scripts/deploy-cs2.sh`, `infra/game-server/README.md` |
| Demo durable stub | напр. `data/demos/` + `demo_files.durable_uri` |

**Минимальные API (ориентир):**

- `POST /api/v1/internal/cs2/events`
- `POST /api/v1/matches` (create/assign server) — по необходимости
- `POST /api/v1/matches/{id}/judge/review-request`
- `POST /api/v1/matches/{id}/judge/review-resolve`
- `POST /api/v1/matches/{id}/commands/{pause|resume|forfeit}` или через judge/resolve
- `GET /api/v1/matches/{id}` (status, score, review, desired/actual pause)
- `GET /api/v1/matches/{id}/snapshot` (platform view) / reconcile trigger

---

## 5. Приёмка

### Primary GATE (обязательно, Fake)

- [x] Контракт задокументирован (events/commands/snapshot)
- [x] Fake CS2 ↔ Platform: score updates from events
- [x] Judge review → pause → continue **и** forfeit работают через API
- [x] Duplicate `event_id` → no double apply
- [x] Out-of-order / gap `sequence` → обнаружение + snapshot reconcile (не silent corrupt)
- [x] Tests A–E (Fake): Platform restart simulation, Agent N/A or stub, duplicate webhook, OOO webhook, judge×round race
- [x] STK.Bridge проект собирается (или чёткий blocker с причиной + stub compile path)
- [x] `deploy-cs2.sh` + README существуют
- [x] Demo durable stub: после «match complete» есть `durable_uri` / файл не только «на fake disk»
- [x] `verify.ps1` включает новые тесты
- [x] Owner smoke primary ≤ 15 мин по инструкции (`workers/developer/notes/TZ002-OWNER-SMOKE.md`)

### Live smoke (опционально / blocked без VPS)

- [ ] CS2 VPS: MatchZy + Bridge → real webhook → pause via API
- [ ] GOTV demo → durable copy
- [x] Статус в CURRENT: `live_smoke=blocked` (нет VPS / SSH @owner)

---

## 6. Runbook

- `workers/developer/notes/TZ002-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ002-NEW-CHAT.md`
- Промптов: **M = 8** (P8 = GATE)

---

## 7. Паритет

Не применимо.

---

## Контекст

- TZ001 Foundation уже даёт: FastAPI layers, MySQL, outbox, correlation_id, compose
- [docs/INVARIANTS.md](../docs/INVARIANTS.md) §3–6, §9, §13, §16
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) §10–11
- [docs/TECH-STACK.md](../docs/TECH-STACK.md) §5 CS2
- [docs/DECISIONS.md](../docs/DECISIONS.md) ADR-010, 023, 026–029, 034
