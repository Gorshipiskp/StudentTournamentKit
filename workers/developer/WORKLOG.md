# WORKLOG — developer

> Архив старше 3 дней → `worklog_archives/WORKLOG-YYYY-MM.md`

---

## 2026-08-11 — TZ002 P8/8 GATE done

- Failure A–E: `apps/api/tests/test_failures_a_e.py` (B = skip → Production / Agent)
- Score bump → `match.version` (гонка E с late `round_end`)
- `scripts/verify.ps1` / `.sh`: artifacts + compose + pytest + fake self-test
- Owner smoke: `workers/developer/notes/TZ002-OWNER-SMOKE.md`
- ROADMAP этап 1 primary closed; **`live_smoke=blocked`** (нет VPS)
- pytest: 35 passed, 1 skipped
- **Стоп:** коммит только `@owner`; дальше TZ003 Production Slice

## 2026-08-11 — TZ002 P7/8 done

- `scripts/deploy-cs2.sh` + `.ps1` dry-run; `infra/game-server/README.md` runbook
- `demo_files` + finalize → `data/demos/`; Fake `finalize-demo`; pytest 31 passed
- `.env.example`: CS2 + `DEMO_DURABLE_ROOT`; live_smoke still blocked without VPS
- **Стоп:** P8 (Failure A–E + GATE) — новый чат

## 2026-08-11 — TZ002 P6/8 done

- `infra/game-server/plugins/STP.Bridge/`: csproj, config, webhook/HMAC, sequence, heartbeat, command listener stubs
- README + recon links CSS/MatchZy; **BUILD BLOCKER**: нет `dotnet` в PATH → checklist для VPS
- **Стоп:** P7 (deploy-cs2 + demo durable) — новый чат

## 2026-08-11 — TZ002 P5/8 done

- `game_servers` registry + assign; GetSnapshot reconcile чинит score/pause/sequence
- heartbeat → `last_heartbeat`; pytest 29 passed
- **Стоп:** P6 (STP.Bridge C# skeleton) — новый чат

## 2026-08-11 — TZ002 P4/8 done

- Judge API: review-request / review-cancel / review-resolve (continue|forfeit)
- ReviewStatus FSM; на `round_start`+buy → PauseMatch; MatchStatus остаётся `live`
- Optimistic `version` + 409 на stale/completed; pytest 25 passed
- **Стоп:** P5 (registry + snapshot reconcile) — новый чат

## 2026-08-11 — TZ002 P3/8 done

- `game_commands` (requested→sent→confirmed|failed); migration `0003_game_commands`
- API: `POST .../commands/{pause|resume|forfeit}`; desired до ack, actual после confirmed
- `GET match`: `split_brain`; ответ явно `confirmed` / `http_200_means_applied=false`
- Idempotent `command_id`; pytest 19 passed (unit + Fake integration)
- **Стоп:** P4 (Judge review flow) — новый чат

## 2026-08-11 — TZ002 P2/8 done

- `POST /api/v1/internal/cs2/events` + HMAC; normalize → Match apply
- `event_id` UNIQUE (`game_events`); duplicate → 200 no-op; sequence gap/OOO → reconcile_needed
- `POST/GET /api/v1/matches`; outbox на status/score
- Alembic `0002_game_slice`; pytest OK (unit + MySQL integration)
- **Стоп:** P3 (commands pause/resume/forfeit) — новый чат

## 2026-08-11 — TZ002 P1/8 done

- Контракт: `infra/game-server/CONTRACT.md` (events, commands, snapshot, HMAC, sequence, command_id)
- Fake: `tools/fake-cs2/` — run / emit-rounds / self-test / post-probe; pytest 3 passed
- Схемы: `apps/api/app/domain/game_integration/schemas.py` (под P2)
- post-probe → `POST /api/v1/internal/cs2/events` дал 404 (ожидаемо до ingest)
- **Стоп:** P2 (Ingest → Match FSM) — новый чат

## 2026-08-11 — TZ002 старт

- TZ001 GATE закрыт (Foundation)
- CURRENT_TASK → TZ002 Game Slice; ждать P1/8

## 2026-08-11 — TZ001 Foundation

- P1–P5 done; verify + owner smoke OK
