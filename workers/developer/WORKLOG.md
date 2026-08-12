# WORKLOG — developer

> Архив старше 3 дней → `worklog_archives/`

---

## 2026-08-13 — Overlay lab panel

- `/overlay-lab`: ручной вызов FX/сцен/счёта; опционально push на матч
- API `POST /matches/{id}/overlay/fx`

## 2026-08-13 — Round win FX visible

- round_start больше не затирает FX победы; round_win крупнее (~6.5с)
- EventFx: TTL от момента получения в браузере

## 2026-08-13 — Sequence rewind after Bridge restart

- Platform: rewind ≥10 → apply (не дропать round_end); snapshot может понизить last_sequence
- Bridge 0.3.3: sequence.txt persist; live match repaired from snapshot

## 2026-08-13 — Bridge 0.3.2 round_end always

- Не глотать round_end на warmup/ошибке GameRules — иначе нет счёта и FX
- install-local-cs2-plugins: DLL поставлен на DS

## 2026-08-13 — Bridge round from game (0.3.1)

- Warmup → round 0; no round_* webhooks in warmup; GetSnapshot refreshes from CCSGameRules
- Platform: round_start+warmup не переводит в live; reconcile warmup → round 0

## 2026-08-13 — Organizer score sync

- Кнопка «С сервера»: GetSnapshot с CS2 → матч + overlay (сброс ручных overrides счёта)
- Ручная запись — отдельно; POST `/score-sync` `from_server=true` по умолчанию
- Тест: stale 0:1 r6 → warmup 0:0

## 2026-08-13 — Branding logo cache bust

- logo/bg URL `?v=<hash>`; admin preview uses version; ETag on asset GET

## 2026-08-12 — dev-remote MediaMTX

- `dev-remote.ps1` поднимает `mediamtx` (`--profile whip`); `-SkipMediamtx` чтобы пропустить
- README scripts обновлён

## 2026-08-12 — Admin UI simplify

- Action-first admin: no guide block; delay under «Дополнительно»
- Stepper mobile-only; shorter shell/rail; MatchOps compact links
- docs/alpha/organizer + dashboard README; build OK

## 2026-08-12 — Director UI simplify

- Scenes-first console; problems-only health; more folded (score/delay/audit)
- Removed dock / filters / duplicate summary; build OK

## 2026-08-12 — Overlay CS2 live FX

- Bridge 0.3.0: bomb_planted / defuse_start / defused / exploded + round winner
- API `data.fx` via live_fx; EventFx UI (timer, plant, defuse, explode, round win)
- CONTRACT + OVERLAY-CONTRACT; tests green; Bridge builds

## 2026-08-12 — BMM tokens on all frontends

- `packages/ui-tokens` (Sora · bone/amber · near-black) + Vite alias `@stk/ui-tokens`
- dashboard / judge / overlay(+watch) restyled; OBS canvas transparent
- builds + judge/overlay tests green

## 2026-08-12 — Overlay restyle P4/4 (wave closed)

- ScoreFlash on ingame/break/winner + watch; debug chip only `?debug=1`
- OWNER-SMOKE note; director.md visual checks; README P1–P4 closed
- build + vitest OK

## 2026-08-12 — Overlay restyle P3/4

- BrandMark on full-screen scenes; brand wash/logo badge; denser ingame HUD (A/B rails)
- aria-live score; reduced-motion; watch inherits brand colors
- build + vitest OK

## 2026-08-12 — Overlay restyle P2/4

- `/watch` cinema: scoreboard A/B accents, wait card, M/F hotkeys, tech tag
- App boot/deny under campus tokens; overlay no longer remounts on every version tick
- Intro/winner delayed enter; build + vitest OK

## 2026-08-12 — Overlay scenes restyle P1/4

- Campus broadcast: Manrope + Barlow Condensed, teal/campus gold, shared `.ov-panel`
- All 6 OBS scenes + OverlayView chrome; canvas stays transparent
- Waiting copy «Игра»; watch fonts aligned; build + vitest OK

## 2026-08-12 — Director UI/UX redesign

- Light broadcast console: RU scene buttons, health grid, scoreboard header
- Override → «Правка табло»; delay/checklist fold; toasts; agent offline callout

## 2026-08-12 — Commentator /watch UI redesign

- Cinema watch UI: scoreboard, scene, live pill, unmute/fullscreen, auto-hide chrome
- Human waiting/errors (no WHIP jargon); overlay OBS transparency unchanged

## 2026-08-12 — Judge UI/UX redesign

- Light mobile field panel: scoreboard, sticky dock actions, forfeit confirm
- Human errors/hints; live WS badge; boot/deny polish
- Labels synced in docs/alpha/judge.md + README

## 2026-08-12 — Admin UI iteration 2

- Shell: rail step nav, loading dim, sticky footer CTA
- List: search, collapsible guide, next-action hints
- Teams/Bracket sticky bars; regenerate confirm; MatchOps auto-links after start

## 2026-08-12 — Admin UI/UX redesign

- Light ops shell: AdminShell, AdminStepper, Toast, ConfirmDialog
- Pages: login/list, teams (progress + inline rename), bracket columns, MatchOps labels, branding preview
- Routes `/admin*` unchanged; director dark theme preserved via scoped `.admin-app`

## 2026-08-12 — TZ010 P6 GATE

- `verify.ps1` баннер TZ010 + артефакты hub/recovery/update/smoke/recon → **VERIFY OK**
- OWNER-SMOKE finalized **gate_ready**; tasks/010 gate_ready
- @owner → `production_ready=done`; коммиты @owner; TL: Twitch / BestTvGU

## 2026-08-12 — TZ010 P5 Second tournament + smoke draft

- [TZ010-OWNER-SMOKE.md](notes/TZ010-OWNER-SMOKE.md): draft ≤45 мин (hub nav + 2nd Fake + recovery drill)
- Hub: чеклист второго турнира + health one-liner; artifact list для verify P6
- Дальше P6 verify banner + GATE; **стоп**; коммиты @owner

## 2026-08-12 — TZ010 P4 Update path

- [docs/UPDATE.md](../../docs/UPDATE.md): git pull → migrate → profiles → /ready; F2 `.env`
- Pointers: hub, scripts/README, infra/platform, mediamtx; ROADMAP
- Compose `--profile whip --profile webrtc config` OK; `.env.example` без schema-дыр
- Дальше P5 second tournament + OWNER-SMOKE draft; **стоп**; коммиты @owner

## 2026-08-12 — TZ010 P3 Recovery

- [docs/PRODUCTION-RECOVERY.md](../../docs/PRODUCTION-RECOVERY.md): симптом→действие (Platform/Agent/OBS/Bridge/overlay/WHIP)
- Failure B: **done** (Go reconciler + pointer); не defer; pytest `test_failures_a_e` 5 passed
- Hub/ARCHITECTURE/INVARIANTS/director pointers
- Дальше P4 update path; **стоп**; коммиты @owner

## 2026-08-12 — TZ010 P2 Production hub

- [docs/PRODUCTION-RUNBOOK.md](../../docs/PRODUCTION-RUNBOOK.md): день матча Fake + второй турнир + оглавление
- Pointers: ALPHA-RUNBOOK, ALPHA-LIVE, alpha/{organizer,director,judge}, ROADMAP этап 7
- G2: live_whip в сводке Alpha; F3/F4 OK
- Дальше P3 recovery; **стоп**; коммиты @owner

## 2026-08-12 — TZ010 P1 RECON

- [TZ010-RECON.md](notes/TZ010-RECON.md): нет PRODUCTION-RUNBOOK hub; alpha docs разрознены
- Failure B: **уже покрыт** `reconciler_test.go` — P3 только человеческий recovery, без Agent redesign
- Дальше P2 hub; **стоп**; коммиты @owner

## 2026-08-12 — TZ010 runbook (Production Ready)

- ТЗ [tasks/010_PRODUCTION-READY.md](../../tasks/010_PRODUCTION-READY.md) + ранбук M=6 + NEW-CHAT
- Фокус: hub runbook, recovery, git pull update, второй турнир за часы; Fake CI
- СТОП кода — открыть Developer с [TZ010-NEW-CHAT.md](notes/TZ010-NEW-CHAT.md) P1/6 (после TL/owner приоритета)

## 2026-08-12 — TZ011 P6 GATE gate_ready

- `verify.ps1` баннер TZ011 + profile whip; VERIFY OK (119 pytest; MediaMTX не обязателен)
- OWNER-SMOKE финал; tasks/011 = gate_ready; ALPHA-LIVE live_whip ready/gate_ready
- `live_whip=done` только после @owner; СТОП коммиты @owner; TL Twitch/TZ010

## 2026-08-12 — TZ011 P5 docs/scripts deprecate FFmpeg live

- ALPHA-LIVE: трек `live_whip=ready`; `live_webrtc` deprecated
- director.md / Agent §4d / templates / webrtc README — канон WHIP
- `live-cs2-local` / `dev-remote`: нет `--live-webrtc`; печать WHIP; real OBS = scenes only
- `TZ011-OWNER-SMOKE.md` draft; health `components.whip` (informational)
- **Стоп — P6 новый чат** (verify + owner GATE); коммиты @owner

## 2026-08-12 — TZ011 P4 /watch WHEP

- `whepClient.ts` + `fetchWhepPlay`; default `media=whep`; Fake=`?media=fake`; mock=`?mock=1`
- UX: «Режиссёр ещё не начал эфир (WHIP)» + retry; overlay WS без изменений
- vitest watchAuth/whep helpers 9 OK
- **Стоп — P5 новый чат** (docs/scripts deprecate live-ffmpeg); коммиты @owner

## 2026-08-12 — TZ011 P3 whip/whep credentials API

- `POST …/whip-publish` (organizer), `POST …/whep-play` (commentator.watch), `POST …/internal/mediamtx-auth`
- Path `stk/<matchId>`; HMAC bearer (`MEDIAMTX_AUTH_SECRET`); WHEP cap ≤2 → 429
- Tests: `test_mediamtx_credentials_unit` + `test_whip_credentials_integration` (8 passed)
- **Стоп — P4 новый чат** (`/watch` WHEP); коммиты @owner

## 2026-08-12 — TZ011 P2 CONTRACT + ADR-037

- ADR-037 accepted in DECISIONS; ADR-022 superseded **for live**; ADR-008 уточнён
- WEBRTC-CONTRACT: protocol **1** Fake / **2** WHIP→MediaMTX→WHEP; credentials shape `whip-publish` / `whep-play` (F7/F9)
- TECH-STACK §4.1 + ARCHITECTURE §13 — минимальный diff
- **Стоп — P3 новый чат** (API handlers); коммиты @owner

## 2026-08-12 — TZ011 P1 spike MediaMTX / WHIP-WHEP

- Compose profile `whip` + `infra/mediamtx/` (v1.12.2); `.env.example` MEDIAMTX_*
- Lab: testsrc RTSP → path `stk/m_spike` → WHEP page **видео OK** (`ice: connected`)
- [TZ011-SPIKE.md](notes/TZ011-SPIKE.md): URL, ICE, WHIP∥Twitch = не один Service (dual-output)
- [ADR-037-DRAFT.md](notes/ADR-037-DRAFT.md) supersede ADR-022 for live
- OBS WHIP publish — @owner; **стоп — P2 новый чат**; коммиты @owner

## 2026-08-12 — TZ011 runbook (OBS WHIP)

- ТЗ [tasks/011_OBS-WHIP.md](../../tasks/011_OBS-WHIP.md) + ранбук M=6 + NEW-CHAT
- Номер **011**: TZ010 оставлен под Production Ready (индекс tasks)
- Канон: MediaMTX на Platform; Fake P2P для CI; FFmpeg/VC → legacy
- СТОП кода — открыть Developer с [TZ011-NEW-CHAT.md](notes/TZ011-NEW-CHAT.md) P1/6

## 2026-08-12 — live-cs2-local real-mode audit

- `live-cs2-local.ps1`: требует CS2_WEBHOOK_SECRET / CS2_INSTALL_DIR / organizer pass из `.env` (без тихого placeholder)
- В `.env` добавлены CS2_INSTALL_DIR + порты; прогон: матч `m_live_cs2` + `srv_local` live; Bridge `stk-bridge`; heartbeat в DB
- Fake не используется; 404 match_id больше не актуален после скрипта
- СТОП — @owner: connect + раунд; коммиты @owner

## 2026-08-12 — live-cs2-local.ps1 (owner UX)

- `scripts/live-cs2-local.ps1`: один запуск — .env, API, матч, assign, start-live, Bridge config, optional DS
- README / LOCAL-CS2 / OWNER-SMOKE / ALPHA-LIVE → скрипт как primary path
- СТОП — коммиты @owner

## 2026-08-12 — TZ009 P6 GATE gate_ready

- `TZ009-OWNER-SMOKE.md` — исполнимый чеклист + curl/PowerShell
- tasks/009 = **gate_ready**; ALPHA-LIVE / ROADMAP: ждут @owner для `live_cs2_local=done` (F5)
- Причина отсрочки: CS2 DS не отвечал на `:27099` в сессии (API `:8000` ok; Bridge DLL на Z:\ есть)
- VERIFY OK с P5; VPS/Twitch не в GATE
- СТОП — @owner: TZ009-OWNER-SMOKE; коммиты @owner; TL: Twitch или TZ010

## 2026-08-12 — TZ009 P5 verify Fake

- `verify.ps1` баннер/артефакты TZ009 (OWNER-SMOKE, RECON, start_match, Bridge GameScoreReader); **без** CS2 DS
- `.\scripts\verify.ps1` → **VERIFY OK — TZ009** (pytest 77+skip, fake-cs2, FE builds, go test)
- scripts/README note TZ009
- СТОП — P6 OWNER-SMOKE + GATE в новом чате; коммиты @owner

## 2026-08-12 — TZ009 P4 docs + smoke draft

- `TZ009-OWNER-SMOKE.md` (≤30 мин): DS → Bridge → start-live → счёт
- LOCAL-CS2-DS § Live-матч; ALPHA-LIVE-TRACKS §1 → TZ009 smoke; organizer: Fake vs локальный сервер
- СТОП — P5 verify (Fake, без обязательного DS) в новом чате; коммиты @owner

## 2026-08-12 — TZ009 P3 live start path

- `start_match_live` + `POST /api/v1/matches/{id}/start-live` (нужен assign + endpoint + secret; не srv_fake)
- Best-effort `LoadMatch` на Bridge; ответ с `bridge_config` (MatchId/ServerId без секрета)
- Dashboard: кнопка «Старт на локальном сервере»; Fake start без регрессии
- README game-server § Live локальный DS; unit `test_match_ops_unit` 7 passed
- СТОП — P4 docs/OWNER-SMOKE draft в новом чате; коммиты @owner

## 2026-08-12 — TZ009 P2 Bridge events

- CSS `RegisterEventHandler` → `round_start` / `round_end` (CONTRACT); CT→team_a, T→team_b via `CTeam.Score`
- `WebhookClient`: warn при non-2xx / transport (без секрета); snapshot из `MatchLiveState`
- `dotnet build` Release OK (net8 + API 1.0.340); DLL → LOCAL-CS2 plugins/STK.Bridge (0.2.0)
- Live DS **не** был запущен (`:27099` timeout); API `:8000` OK — owner: рестарт dedicated + round smoke
- СТОП — P3 live path в новом чате; коммиты @owner

## 2026-08-12 — TZ009 P1 recon

- `TZ009-RECON.md`: карта пробелов Fake vs DS; GATE = `heartbeat` + `round_end` (или score+раунд); целевой P2 + `round_start`
- Хуки P2: CSS game events (primary) · MatchZy HTTP log → Bridge adapter (alt); ссылки без выдуманных API
- LOCAL-CS2-DS чеклист готовности (gameinfo, plugins, 27015/27099, config/secret)
- Bridge README → TZ009-RECON; runbook P1=done
- СТОП — P2 в новом чате (не реализовывать хуки здесь)

## 2026-08-12 — TZ009 runbook (Live CS2 Local)

- tasks/009_LIVE-CS2-LOCAL.md + PROMPT-RUNBOOK M=6 + NEW-CHAT
- Production Ready сдвинут на **TZ010**
- СТОП — ждать новый чат P1/6 (TZ009-NEW-CHAT)
## 2026-08-12 — live blockers → ready

- `live_obs` = done (с TZ008); `live_cs2_local` / `live_twitch` = **ready**
- ALPHA-LIVE-TRACKS: раздел «Пробный матч — что делать тебе»
- СТОП — прохождение треков @owner; коммиты @owner
## 2026-08-12 — TZ008 GATE closed

- @owner: real OBS + live WebRTC / `/watch` OK → `live_webrtc=done`
- Encode bump: 1080p, 3500k, deadline=good, cpu-used=4 (пересобери Agent)
- TZ004 optional closed; ROADMAP People live done; next **TZ009**
- СТОП — коммиты @owner; TL: открыть TZ009
## 2026-08-12 — TZ008 P5 GATE gate_ready

- `TZ008-OWNER-SMOKE.md` (≤25 мин Virtual Cam → `/watch`)
- VERIFY OK TZ008; VCam 1-frame OK; Agent `--live-webrtc` path готов
- Full `live_webrtc=done` после @owner `/watch` (Docker Desktop down в сессии P5)
- Не production (TZ009); коммиты только @owner
- СТОП — owner: TZ008-OWNER-SMOKE

## 2026-08-12 — TZ008 P4 tests + verify

- Unit: FakeTrackRunBrief + live_track args/ffmpeg errors (без OBS)
- `verify.ps1` → **VERIFY OK — TZ008** (Fake CI; OBS не требуется)
- scripts/README: TZ008 note
- СТОП — P5 OWNER-SMOKE + GATE в новом чате

## 2026-08-12 — TZ008 P3 docs + operator

- Agent README §4c Live Virtual Cam (шаги); `docs/alpha/director.md` блок RU
- `ALPHA-LIVE-TRACKS` § live_webrtc = TZ008 steps; templates §3 + cross-links
- `live_webrtc` ещё **blocked** до P5 owner smoke
- СТОП — P4 tests + verify в новом чате

## 2026-08-12 — TZ008 P2 live publisher

- `live_track.go`: FFmpeg dshow → VP8 IVF → `TrackLocalStaticSample`; clear errors if ffmpeg/cam missing
- Flags: `--live-webrtc`, `--webrtc-device`, `--webrtc-ffmpeg` (mutex with `--fake-webrtc`)
- go test ./... OK; smoke: live publisher starts with Virtual Cam
- СТОП — P3 docs/operator guides в новом чате

## 2026-08-12 — TZ008 P1 contract + spike

- `WEBRTC-CONTRACT` § Live source (Fake CI / Live Virtual Cam; F1–F6)
- Spike Windows: device **OBS Virtual Camera**; 1-frame FFmpeg OK (1920x1080)
- `webrtc/README`: list_devices + IVF pipe + `-rtbufsize`; flags draft
- Agent README § 4c flags table; capture code = P2
- СТОП — P2 Agent live publisher в новом чате

## 2026-08-12 — TZ008 opened (Live WebRTC)

- ТЗ `tasks/008_LIVE-WEBRTC.md` + runbook M=5 + NEW-CHAT P1
- Sync: ROADMAP (TZ009=Production Ready), ALPHA-LIVE-TRACKS, tasks/README, WEBRTC-CONTRACT § Live, CURRENT S009
- СТОП — код только с P1 в новом чате (`TZ008-NEW-CHAT.md`)

## 2026-08-12 — TZ007 P6 GATE gate_ready

- `TZ007-OWNER-SMOKE.md` (≤40 мин Fake + чеклист приёмки)
- `verify.ps1` → **VERIFY OK — TZ007**; `alpha-dry-run.ps1` OK
- tasks/007 status=gate_ready; ROADMAP этап 6; live_*=blocked; CODE_CHANGE_BOARD
- Full GATE close после @owner smoke + post-mortem; не production (TZ009)
- СТОП — коммиты только @owner; owner: TZ007-OWNER-SMOKE

## 2026-08-12 — TZ007 P5 live tracks + post-mortem

- `docs/ALPHA-LIVE-TRACKS.md`: live_cs2_local / live_obs / live_twitch / live_webrtc = **blocked** + шаги и ссылки
- `docs/alpha/POST-MORTEM-TEMPLATE.md`; ссылки из ALPHA-RUNBOOK
- Live не требуется для Primary GATE
- СТОП — P6 verify + OWNER-SMOKE + GATE в новом чате

## 2026-08-12 — TZ007 P4 dry-run gaps

- Прогон `alpha-dry-run.ps1`: **ALPHA DRY-RUN OK** (verify 75 pytest); E2E блокеров нет
- Soft: API down на probe = ожидаемо; баннер verify ещё TZ006 → P6
- Fix: precheck `docs/alpha/*.md`; human steps → памятки; README § итог P4
- СТОП — P5 live tracks + post-mortem template в новом чате

## 2026-08-12 — TZ007 P3 operator guides

- `docs/alpha/organizer.md` · `director.md` · `judge.md` (RU, день Alpha, ≤2 стр.)
- Ссылки из ALPHA-RUNBOOK; cross-links dashboard / templates / judge / BROADCAST-*
- СТОП — P4 dry-run gap fixes в новом чате

## 2026-08-12 — TZ007 P2 alpha-dry-run

- `scripts/alpha-dry-run.ps1`: .env + Alpha artifacts + optional `-Migrate` + subprocess `verify.ps1` + human Fake E2E checklist
- `scripts/README.md` § alpha-dry-run; ссылка из ALPHA-RUNBOOK
- Прогон: **ALPHA DRY-RUN OK** (verify 75 pytest + frontends); API probe OK
- СТОП — P3 operator guides RU в новом чате

## 2026-08-12 — TZ007 P1 ALPHA-RUNBOOK

- `docs/ALPHA-RUNBOOK.md`: цель Alpha, роли, порядок дня Fake, ссылки TZ002–006 smokes
- Чеклист приёмки @owner (admin → match → director → judge → overlay/health/audit)
- Frozen: 4 teams single-elim, Fake primary; live blocked
- ROADMAP этап 6 уже in progress; трекер P1=done
- СТОП — P2 `alpha-dry-run.ps1` в новом чате

## 2026-08-12 — TZ007 старт

- TZ006 GATE closed; CURRENT_TASK → TZ007 Alpha; ждать P1/6

## 2026-08-12 — TZ006 P7 GATE closed

- `scripts/verify.ps1` → **VERIFY OK — TZ006** (75 pytest; frontends; agent; 0013 audit)
- `TZ006-OWNER-SMOKE.md` (≤25 мин, Fake OBS); Primary GATE §5 отмечен
- `tasks/006` status=done; ROADMAP этап 5 GATE closed; `live_twitch=blocked`
- Следующий для TL: **TZ007 Tournament Alpha**
- СТОП — коммиты только @owner

## 2026-08-12 — TZ006 P6 Audit log UI

- Director: блок «Журнал действий» (время, актор, действие, результат — RU)
- `GET /audit` публичное чтение для панели; refresh после scene/override + poll
- README + BROADCAST-HEALTH § audit; build OK
- СТОП — P7 verify + OWNER-SMOKE + GATE в новом чате

## 2026-08-12 — TZ006 P5 Director health panel

- Director: блок «Состояние эфира» (poll health) + delay checklist на одной странице
- RU статусы; agent offline / OBS offline — понятные подсказки; scene/override без регрессии
- Dashboard build OK
- СТОП — P6 audit UI в новом чате

## 2026-08-12 — TZ006 P4 Match health API

- `GET /api/v1/matches/{id}/health` — platform/agent/obs/overlay/game/broadcast
- Enum HEALTHY|DEGRADED|OFFLINE|UNKNOWN; Fake OBS → overall HEALTHY; `docs/BROADCAST-HEALTH.md`
- Unit + integration; overlay.updated_at для age
- СТОП — P5 director health panel в новом чате

## 2026-08-12 — TZ006 P3 Audit log backend

- Alembic `0013_match_audit_log`; `write_audit` + repo
- Writers: judge review/resolve/forfeit, director scene/override, organizer start, system.round_end
- `GET /api/v1/matches/{id}/audit` (organizer); unit + integration tests
- СТОП — P4 health aggregate в новом чате

## 2026-08-12 — TZ006 P2 Overlay scene polish

- 6 layout-компонентов: `apps/overlay/src/lib/scenes/*` (waiting/intro/teams/ingame/break/winner)
- `tournament_name` в overlay merge + snapshot; branding/watermark сохранены
- Build + vitest OK; unit merge OK
- СТОП — P3 audit log backend в новом чате

## 2026-08-12 — TZ006 P1 Broadcast delay checklist

- `docs/BROADCAST-DELAY.md` — OBS Stream Delay v1, ADR-024, без FFmpeg/Agent automation
- `GET /matches/{id}` → `configured_broadcast_delay_seconds` из tournament settings
- Director UI: блок «Задержка Twitch» + RU checklist; ссылки на templates README §3
- Dashboard build OK; pytest delay hint (skip без MySQL)
- СТОП — P2 overlay polish в новом чате

## 2026-08-12 — TZ006 старт

- TZ005 GATE closed; CURRENT_TASK → TZ006 Broadcast; ждать P1/7

## 2026-08-12 — TZ005 P7 GATE closed

- `scripts/verify.ps1` → **VERIFY OK — TZ005** (96 pytest; frontend builds; agent)
- `TZ005-OWNER-SMOKE.md` (≤25 мин, Fake only)
- Primary GATE §5 отмечен; `tasks/005` status=done; ROADMAP этап 4 GATE closed
- Следующий для TL: **TZ006 Broadcast Slice**
- СТОП — коммиты только @owner

## 2026-08-12 — TZ005 P6 Multi-tournament + wizard polish

- WizardNav на admin/teams/bracket/branding; пустые состояния (нет команд / неполная сетка)
- Smoke: `test_multi_tournament_smoke.py` — 2 published cups, teams/matches/invites изолированы
- `apps/dashboard/README.md` § «Admin: как провести турнир»
- СТОП — P7 verify + OWNER-SMOKE в новом чате

## 2026-08-12 — TZ005 P5 Fake start + staff links

- `POST /matches/{id}/start` (organizer) → live + ingame; Fake без CS2 VPS
- `POST /matches/{id}/staff-links` → judge/commentator invites + URLs
- Bracket UI: MatchOps — Старт + копирование ссылок (режиссёр/судья/комментатор)
- Pytest unit+integration; dashboard build OK
- СТОП — P6 в новом чате

## 2026-08-12 — TZ005 P4 Branding → overlay

- `tournament_branding` + Alembic 0012; PUT multipart logo/colors; public GET logo/bg
- Overlay merge `data.branding`; UI logo + accent; watermark STK сохранён
- СТОП — P5 в новом чате

## 2026-08-12 — TZ005 P3 / P2 / P1

- Bracket; teams/players; organizer auth + tournament CRUD

## 2026-08-12 — TZ004 / TZ003

- People / Production GATE
