# TZ002 — PROMPT RUNBOOK · Game Slice

> ТЗ: [tasks/002_GAME-SLICE.md](../../../tasks/002_GAME-SLICE.md)  
> База: TZ001 Foundation (done)  
> **M = 8** · P8 = GATE · 1 чат = 1 промпт

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/8 | Контракт CS2↔Platform + Fake Game Server | **done** | 2026-08-11 |
| 2/8 | Ingest webhooks → Match FSM (score/status) | **done** | 2026-08-11 |
| 3/8 | Commands: pause/resume/forfeit + command_id/ack | **done** | 2026-08-11 |
| 4/8 | Judge review flow end-to-end (Fake) | **done** | 2026-08-11 |
| 5/8 | Game server registry + assign + snapshot reconcile | **done** | 2026-08-11 |
| 6/8 | STK.Bridge skeleton (C#) | **done** | 2026-08-11 |
| 7/8 | deploy-cs2.sh + demo durable stub | **done** | 2026-08-11 |
| 8/8 | Failure A–E + verify + GATE | **done** | 2026-08-11 |

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/8 | §0 · §1 Fake/contract · §2 F1 F2 F5 · §4 |
| 2/8 | §2 F3 F5 F6 · §4 ingest · INVARIANTS §6 |
| 3/8 | §2 F4 F7 · ARCHITECTURE commands |
| 4/8 | §0 judge · §2 F3 · VISION judge workflow |
| 5/8 | §4 registry/snapshot · INVARIANTS §4 §9 |
| 6/8 | §1 Bridge · §2 F1 · TECH-STACK §5 |
| 7/8 | §1 deploy/demo · §2 F8 · ADR-034 |
| 8/8 | §3 · §5 Приёмка · INVARIANTS §16 |

---

## P1/8 — Контракт + Fake Game Server

### Делать

- Документ контракта (короткий): `docs/CS2-CONTRACT.md` **или** `infra/game-server/CONTRACT.md`
  - events: типы, `event_id`, `sequence`, HMAC headers
  - commands: PauseMatch, ResumeMatch, ForfeitMatch, GetSnapshot + `command_id` + ack shape
  - snapshot JSON
- Реализовать **Fake Game Server** (`tools/fake-cs2/`):
  - конфиг: platform URL, match_id, server_id, webhook secret
  - умеет: emit round_start/round_end/score, accept pause/resume/forfeit, return snapshot, ack
- README: как запустить fake против local API (API ingest может быть stub-заглушкой до P2 — тогда fake пишет в файл/stdout **и** готов POST на `/internal/cs2/events`)

### Не делать

- Полный Match FSM в Platform (P2)
- Judge UI
- Реальный CS2
- Коммит без @owner

### DoD

- [x] Контракт в репо, согласован с INVARIANTS §6
- [x] Fake запускается одной командой
- [x] Fake может отправить тестовый POST (даже если API пока 404 — зафиксировать ожидаемый URL)
- [x] Pytest или script smoke на fake self-check (state machine fake)

### Проверки

```text
# run fake --help / self-test
# optional: curl fake health
```

---

## P2/8 — Ingest → Match FSM

### Делать

- `POST /api/v1/internal/cs2/events` + HMAC verify
- Нормализация → domain events (без MatchZy типов в domain)
- Match aggregate: обновить score/round/status из events
- `event_id` UNIQUE в той же транзакции, что update; duplicate → 200 no-op
- `sequence`: хранить last_sequence; gap/OOO → флаг/результат reconcile needed (не молча перетирать историю)
- Outbox на значимых transitions
- Тесты: happy path score; duplicate event_id

### Не делать

- Judge flow (P4)
- Commands к fake (P3)
- Bridge C#

### DoD

- [x] Fake → Platform: score виден в `GET match`
- [x] Duplicate event не удваивает score
- [x] Domain свободен от RCON/MatchZy строк
- [x] Pytest зелёный

---

## P3/8 — Commands + command_id / ack

### Делать

- Platform → Fake: Pause / Resume / Forfeit с `command_id`
- Таблица/модель `game_commands` (status: requested→sent→confirmed|failed)
- Desired vs actual pause flags на match
- Fake: ack + optional event `tech_pause_started` / unpaused
- API не считает успехом один HTTP 200 без confirmed (или явно: accepted vs confirmed в ответе)
- Тесты: idempotent повтор того же `command_id`

### Не делать

- Полный judge orchestration (P4) — можно дергать commands напрямую
- Live RCON

### DoD

- [x] Pause/resume/forfeit через API меняют desired; после ack — actual
- [x] Повтор command_id безопасен
- [x] Split-brain (desired≠actual) виден в GET match

---

## P4/8 — Judge review flow (Fake)

### Делать

- Endpoints judge: `review-request` (cancellable), `review-resolve` {continue|forfeit}
- ReviewStatus: none→requested→pause_pending→paused→resolved
- Интеграция с Fake: при `requested`, на следующем `round_start`+buy Fake/Platform инициирует pause (как в VISION)
- MatchStatus остаётся `live` во время tech pause
- Stale resolve на completed → 409/reject
- Optimistic `matches.version` на resolve
- Тесты: continue path; forfeit path; cancel request; race со round event

### Не делать

- Mobile judge UI (достаточно API; curl/httpx в тестах)
- Overlay banner UI (можно поле в match GET)

### DoD

- [x] Полный сценарий review→pause→continue на Fake
- [x] Forfeit завершает match корректно
- [x] MatchStatus ≠ ReviewStatus в модели/API

---

## P5/8 — Server registry + snapshot reconcile

### Делать

- `game_servers` registry (create/list; status available/assigned/…)
- Assign server to match
- `GetSnapshot` command + reconcile: сравнить platform view vs snapshot; починить score/pause при drift
- Heartbeat stub от Fake
- Тесты: после «пропущенного» event — reconcile чинит state

### Не делать

- Auto-provision VPS
- Multi-server scheduler

### DoD

- [x] Assign server работает
- [x] Reconcile после gap sequence восстанавливает согласованность
- [x] Health-ish fields на server (last_heartbeat)

---

## P6/8 — STK.Bridge skeleton (C#)

### Делать

- `infra/game-server/plugins/STK.Bridge/`:
  - csproj CounterStrikeSharp-compatible
  - Plugin entry, config (platform URL, secret, match/server id)
  - Заготовки: webhook client, heartbeat, command listener stubs, sequence counter
  - README: build/publish в plugins folder
- **Recon:** ссылки на актуальную док CSS/MatchZy в README (версии — best effort; не выдумывать API)
- Если сборка в CI невозможна без SDK — document blocker + максимально полный исходник; локальный `dotnet build` если SDK есть

### Не делать

- Полная реализация всех CS2 hooks «вслепую» без контракта
- Править MatchZy
- Overlay

### DoD

- [x] Проект в репо с README
- [x] `dotnet build` успешен **или** явный blocker + checklist для VPS machine
- [x] Конфиг соответствует CONTRACT

---

## P7/8 — deploy-cs2.sh + demo durable

### Делать

- `scripts/deploy-cs2.sh` (+ `.ps1` optional): шаги SteamCMD, CS2DS, Metamod, CSS, MatchZy, copy Bridge, firewall notes, register-to-platform hint
- `infra/game-server/README.md` — операторский runbook
- Demo durable stub: при match complete — copy/metadata → `demo_files.durable_uri` (локальный `data/demos/` ok)
- Fake может «финализировать» fake demo file

### Не делать

- Реальный деплой без SSH владельца (можно dry-run)
- S3

### DoD

- [x] Скрипт и README в репо
- [x] Durable demo path проверяется тестом/скриптом на Fake complete
- [x] `.env.example` дополнен CS2/webhook secret keys

---

## P8/8 — Failure A–E + GATE

### Делать

- Автотесты / сценарии:
  - **A** Platform restart mid-match (Fake continues; after restart reconcile)
  - **B** N/A Agent → skip или stub note (Production TZ); минимум document
  - **C** Duplicate webhook
  - **D** Out-of-order webhook
  - **E** Judge resolve race with round_end
- Расширить `scripts/verify.ps1`
- Owner smoke primary (инструкция в отчёте)
- Обновить ROADMAP § Этап 1 чеклист; CURRENT.md; WORKLOG
- Явно: `live_smoke=blocked` пока нет VPS **или** done если прогнали

### Не делать

- Начинать Production Slice UI
- Scope creep «ещё и overlay»

### DoD (GATE)

- [x] Все пункты §5 Primary GATE
- [x] verify зелёный
- [x] Трекер P1–P8 done
- [x] Отчёт владельцу: как гонять Fake; что нужно для live VPS
- [x] `live_smoke=blocked` (нет VPS / SSH @owner)
- Owner smoke: [TZ002-OWNER-SMOKE.md](TZ002-OWNER-SMOKE.md)

### Owner smoke (primary)

```text
1. compose up + migrate (как TZ001)
2. создать match + assign fake server (API)
3. запустить tools/fake-cs2
4. сымитировать 2–3 раунда → score в GET match
5. review-request → дождаться pause → resolve continue
6. verify.ps1
```

---

## Эскалация

| Ситуация | Куда |
|----------|------|
| Нет .NET SDK для Bridge build | Зафиксировать blocker; не стопать Fake GATE |
| MatchZy API отличается от ожиданий | Recon в README; править только Bridge/adapter |
| Нужен live VPS | @owner — доступ SSH |
| Conflict Frozen | @team-lead |

---

## После GATE

→ **TZ003 Production Slice** (overlay + dashboard + Director Agent + OBS).
