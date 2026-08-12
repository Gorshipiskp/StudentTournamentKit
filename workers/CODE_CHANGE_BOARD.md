# Доска изменений кода (CODE_CHANGE_BOARD)

> **Пишут:** все, кто менял код (developer, devops, …).  
> **Обрабатывает:** scout → `tech-overview/` → архив → очистка.  
> *Scout пока не развёрнут — записи накапливаются до появления роли.*

---

## Ожидают обработки

### 2026-08-12 — Admin UI simplify @developer

- **Пакеты:** `apps/dashboard` Admin* / Teams / Bracket / Branding / MatchOps; alpha/organizer
- **Суть:** action-first organizer UX; fold secondary; mobile stepper only
- **tech-overview:** systems/dashboard-admin

### 2026-08-12 — Overlay CS2 live FX @developer

- **Пакеты:** STK.Bridge 0.3.0; api live_fx/ingest; overlay EventFx; CONTRACT
- **Суть:** bomb + round_win chrome on overlay via `data.fx`
- **tech-overview:** systems/overlay + game-bridge

### 2026-08-12 — BMM ui-tokens all frontends @developer

- **Пакеты:** `packages/ui-tokens`; dashboard/judge/overlay Vite alias + app.css
- **Суть:** near-black · bone · amber · Sora; OBS canvas transparent
- **tech-overview:** systems/ui-tokens

### 2026-08-12 — Overlay UI restyle P1–P4 @developer

- **Пакеты:** `apps/overlay` scenes/WatchPage/App; OVERLAY-UI-OWNER-SMOKE; alpha/director
- **Суть:** campus broadcast look; BrandMark; denser HUD; ScoreFlash; `?debug=1`
- **tech-overview:** systems/overlay

### 2026-08-12 — Admin UI redesign @developer

- **Пакеты:** `apps/dashboard` admin pages + shell/toast/dialog
- **Суть:** human labels, light ops UX, no prompt/confirm
- **tech-overview:** systems/dashboard-admin

### 2026-08-12 — TZ010 P6 gate_ready @developer

- **Пакеты:** `scripts/verify.ps1` TZ010; OWNER-SMOKE gate_ready; tasks/010
- **Суть:** Fake VERIFY OK; production_ready ждёт @owner
- **tech-overview:** systems/ops-runbooks

### 2026-08-12 — TZ010 P5 second tournament @developer

- **Пакеты:** `TZ010-OWNER-SMOKE.md` draft; hub checklist; ROADMAP note
- **Суть:** F6 owner path; verify artifacts listed for P6
- **tech-overview:** systems/ops-runbooks

### 2026-08-12 — TZ010 P4 update @developer

- **Пакеты:** `docs/UPDATE.md`; pointers hub/scripts/infra
- **Суть:** воспроизводимый git pull path; profiles explicit
- **tech-overview:** systems/ops-runbooks

### 2026-08-12 — TZ010 P3 recovery @developer

- **Пакеты:** `docs/PRODUCTION-RECOVERY.md`; pointers hub/ARCH/INVARIANTS/director; docstring B
- **Суть:** human recovery; Failure B already Go (no Agent redesign)
- **tech-overview:** systems/ops-runbooks

### 2026-08-12 — TZ010 P2 hub @developer

- **Пакеты:** `docs/PRODUCTION-RUNBOOK.md`; pointers ALPHA/ROADMAP/alpha/*
- **Суть:** один вход день матча + 2-й турнир; без дублей кликов
- **tech-overview:** systems/ops-runbooks

### 2026-08-12 — TZ010 P1 RECON @developer

- **Пакеты:** `TZ010-RECON.md`; tasks/010 in_progress
- **Суть:** gaps → P2–P6; Failure B = done in Agent tests (docs in P3)
- **tech-overview:** systems/ops-runbooks (когда появится)

### 2026-08-12 — TZ011 P6 gate_ready @developer

- **Пакеты:** `scripts/verify.ps1` TZ011; TZ011-OWNER-SMOKE final; tasks/011 gate_ready; ROADMAP/ALPHA-LIVE notes
- **Суть:** Fake VERIFY OK; live_whip=done после @owner WHIP smoke
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ011 P5 docs/scripts @developer

- **Пакеты:** ALPHA-LIVE, director.md, Agent/templates README, live-cs2-local/dev-remote, TZ011-OWNER-SMOKE, get_match_health whip
- **Суть:** канон без FFmpeg/VC; скрипты не стартуют live-webrtc; smoke draft
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ011 P4 /watch WHEP @developer

- **Пакеты:** `apps/overlay` whepClient, WatchPage, watchAuth media mode, README
- **Суть:** live `/watch` через WHEP; Fake/mock сохранены; статус без publisher = WHIP waiting
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ011 P3 credentials API @developer

- **Пакеты:** `mediamtx_credentials.py`, `whep_sessions.py`, `routers/whip.py`, `.env.example`, tests
- **Суть:** Platform выдаёт WHIP/WHEP URL+bearer; лимит 2 WHEP; MediaMTX authHTTP callback
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ011 P2 ADR + CONTRACT @developer

- **Пакеты:** `docs/DECISIONS.md` ADR-037; `docs/WEBRTC-CONTRACT.md` dual-mode; TECH-STACK §4.1; ARCHITECTURE §13
- **Суть:** live = WHIP/MediaMTX/WHEP; Fake = protocol 1; credentials shape для P3
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ011 P1 MediaMTX spike @developer

- **Пакеты:** `infra/mediamtx/` (+ spike whep.html); compose profile `whip`; `.env.example` MEDIAMTX_*; TZ011-SPIKE; ADR-037-DRAFT
- **Суть:** MediaMTX на Platform skeleton; lab WHEP OK; live-канон to-be WHIP→MTX→WHEP (Fake без MTX)
- **tech-overview:** systems/webrtc-whip (когда появится)

### 2026-08-12 — TZ009 P6 gate_ready @developer

- **Пакеты:** `TZ009-OWNER-SMOKE.md` final; tasks/009 gate_ready; ALPHA-LIVE/ROADMAP notes
- **Суть:** волна P1–P6 закрыта для кода; live_cs2_local=done после @owner DS smoke (F5)
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ009 P5 verify Fake @developer

- **Пакеты:** `scripts/verify.ps1` TZ009 banner + artifacts; scripts/README
- **Суть:** VERIFY OK без CS2 DS; Fake path зелёный
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ009 P4 docs + OWNER-SMOKE draft @developer

- **Пакеты:** `TZ009-OWNER-SMOKE.md`; LOCAL-CS2-DS § Live-матч; ALPHA-LIVE-TRACKS §1; organizer.md
- **Суть:** owner может пройти live_cs2_local по докам; GATE close = P6 после smoke
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ009 P3 live start path @developer

- **Пакеты:** `start_match.py` start_match_live; matches `POST …/start-live`; MatchOps + api.ts; game-server README
- **Суть:** матч live без Fake после register/assign; Fake `/start` сохранён
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ009 P2 Bridge CSS events @developer

- **Пакеты:** `infra/game-server/plugins/STK.Bridge` 0.2.0 (`EventRoundStart`/`End` → `round_*`; `GameScoreReader`; webhook warn-логи); deploy LOCAL-CS2
- **Суть:** GATE event path с DS без fork MatchZy; live smoke ждёт рестарт DS @owner
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ009 opened @developer

- **Пакеты:** tasks/009_LIVE-CS2-LOCAL; TZ009-PROMPT-RUNBOOK M=6; NEW-CHAT; Production Ready → TZ010
- **Суть:** Live CS2 Local wave; Bridge skeleton → webhooks; Fake CI сохранён
- **tech-overview:** systems/live-cs2 (когда появится)

### 2026-08-12 — TZ008 GATE closed @owner/@developer

- **Пакеты:** tasks/008 done; `live_webrtc=done`; encode bump `live_track.go` 1080p/3500k; TZ004 optional closed
- **Суть:** Real OBS + live WebRTC принят @owner; качество улучшено post-GATE; next TZ009
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ008 P5 gate_ready @developer

- **Пакеты:** `TZ008-OWNER-SMOKE.md`; tasks/008 gate_ready; ALPHA-LIVE-TRACKS; verify footer
- **Суть:** VERIFY OK; VCam frame OK; `/watch` E2E отложен (Docker Desktop down) → @owner; не TZ009 close
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ008 P4 tests + verify @developer

- **Пакеты:** `verify.ps1` TZ008 artifacts; `TestFakeTrackRunBrief`; live_track unit
- **Суть:** VERIFY OK без OBS; live_webrtc owner smoke = P5
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ008 P2 live publisher @developer

- **Пакеты:** `webrtc/live_track.go`, `cmd/agent` `--live-webrtc` / `--webrtc-device` / `--webrtc-ffmpeg`
- **Суть:** FFmpeg dshow OBS Virtual Camera → VP8 IVF → Pion; Fake path unchanged
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ008 P1 contract + spike @developer

- **Пакеты:** `docs/WEBRTC-CONTRACT.md` § Live; `webrtc/README.md`; Agent README §4c
- **Суть:** device `OBS Virtual Camera` confirmed; flags draft; capture impl = P2
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ008 Live WebRTC opened @developer

- **Пакеты:** `tasks/008_LIVE-WEBRTC.md`, `TZ008-PROMPT-RUNBOOK.md`, `TZ008-NEW-CHAT.md`; ROADMAP/ALPHA-LIVE-TRACKS; Production Ready → TZ009
- **Суть:** OBS Virtual Cam → Agent → `/watch`; Fake остаётся CI; закрыть `live_webrtc=blocked`
- **tech-overview:** systems/live-webrtc (когда появится)

### 2026-08-12 — TZ007 P1–P6 gate_ready @developer

- **Пакеты:** `docs/ALPHA-RUNBOOK.md`, `docs/ALPHA-LIVE-TRACKS.md`, `docs/alpha/*`, `scripts/alpha-dry-run.ps1`, `verify.ps1` TZ007, `TZ007-OWNER-SMOKE.md`
- **Суть:** Tournament Alpha Fake gate_ready; live_*=blocked; @owner smoke/post-mortem pending; next TZ008
- **tech-overview:** systems/tournament-alpha (когда появится)

### 2026-08-12 — S007 closed / TZ007 opened @team-lead

- **Пакеты:** `tasks/007_TOURNAMENT-ALPHA.md`, `TZ007-PROMPT-RUNBOOK.md`, sprint S008
- **Суть:** Broadcast GATE closed; Alpha E2E runbooks + dry-run
- **tech-overview:** systems/tournament-alpha (когда появится)

### 2026-08-12 — TZ006 GATE closed @developer

- **Пакеты:** verify.ps1 TZ006, TZ006-OWNER-SMOKE, tasks/006 done, ROADMAP этап 5
- **Суть:** Broadcast Primary GATE Fake OBS; live_twitch=blocked; next TZ007
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P6 audit UI @developer

- **Пакеты:** DirectorPage audit list; GET `/audit` public read; README + BROADCAST-HEALTH
- **Суть:** RU журнал действий; refresh после scene/override
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P5 director health UI @developer

- **Пакеты:** `apps/dashboard` DirectorPage health panel + getMatchHealth
- **Суть:** poll health + delay checklist; RU empty states agent/OBS offline
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P4 match health @developer

- **Пакеты:** `GET /matches/{id}/health`, `get_match_health.py`, `docs/BROADCAST-HEALTH.md`
- **Суть:** aggregate HEALTHY/DEGRADED/OFFLINE/UNKNOWN; Fake OBS path
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P3 match_audit_log @developer

- **Пакеты:** alembic 0013, `write_audit`, GET `/matches/{id}/audit`, writers на judge/director/organizer/system
- **Суть:** A10 audit trail; correlation_id; ≥5 action types
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P2 overlay scenes @developer

- **Пакеты:** `apps/overlay/src/lib/scenes/*`, merge `tournament_name`, OVERLAY-CONTRACT
- **Суть:** 6 semi-pro layouts + branding; watermark STP сохранён
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — TZ006 P1 delay checklist @developer

- **Пакеты:** `docs/BROADCAST-DELAY.md`, `apps/dashboard` DirectorPage, `GET /matches` delay hint
- **Суть:** OBS Stream Delay v1 contract + director RU checklist; F7 desired not verified
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — S006 closed / TZ006 opened @team-lead

- **Пакеты:** `tasks/006_BROADCAST-SLICE.md`, `TZ006-PROMPT-RUNBOOK.md`, sprint S007
- **Суть:** Tournament волна закрыта; Broadcast delay/health/audit
- **tech-overview:** systems/broadcast-slice (когда появится)

### 2026-08-12 — Local CS2 DS @owner

- **Пакеты:** `infra/game-server/LOCAL-CS2-DS.md`, `.env.example`, README ссылки
- **Суть:** Windows DS `Z:\cs2_dedicated_server\…` — основной live CS2 для recon/smoke
- **tech-overview:** systems/cs2-dedicated (когда появится)

### 2026-08-12 — TZ005 GATE closed @developer

- **Пакеты:** `scripts/verify.ps1` (TZ005), `TZ005-OWNER-SMOKE.md`, tasks/005 + ROADMAP этап 4
- **Суть:** Tournament Slice primary GATE; Fake match; next TZ006 Broadcast
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P6 multi-tournament + wizard polish @developer

- **Пакеты:** `apps/dashboard` WizardNav + empty states; `test_multi_tournament_smoke.py`; README admin walkthrough
- **Суть:** RU wizard steps; 2 published cups isolated; admin § без жаргона
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P5 Fake start + staff links @developer

- **Пакеты:** `POST /matches/{id}/start`, `/staff-links`, MatchOps UI, dashboard README Fake path
- **Суть:** organizer start→live (Fake); judge/commentator/director URLs copy-paste
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P4 branding → overlay @developer

- **Пакеты:** `tournament_branding` + alembic 0012, branding API, overlay merge/UI, python-multipart
- **Суть:** logo≤2MB + colors → snapshot.branding; public logo URL; watermark STK остаётся
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P3 single-elim bracket @developer

- **Пакеты:** `apps/api` bracket_nodes + manage_bracket, alembic 0011, `BracketPage`
- **Суть:** generate 4/8; PATCH slots; pair ready → create_match; admin UI сетка
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P2 teams + players @developer

- **Пакеты:** `apps/api` teams/players, alembic 0010, `apps/dashboard` TeamsPage
- **Суть:** CRUD команд/игроков по tournament_id; admin UI; изоляция турниров
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ005 P1 organizer auth + tournament CRUD @developer

- **Пакеты:** `apps/api` auth/tournaments, alembic 0009, `apps/dashboard` `/admin`
- **Суть:** instance login → JWT; tournament draft CRUD + publish; admin list UI
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — S005 closed / TZ005 opened @team-lead

- **Пакеты:** `tasks/005_TOURNAMENT-SLICE.md`, `TZ005-PROMPT-RUNBOOK.md`, sprint S006
- **Суть:** People волна закрыта; следующая — Tournament admin/bracket
- **tech-overview:** systems/tournament-admin (когда появится)

### 2026-08-12 — TZ004 P7 GATE @developer

- **Пакеты:** `scripts/verify.*`, `TZ004-OWNER-SMOKE.md`, ROADMAP этап 3, tasks/004 §5
- **Суть:** People GATE closed; fake-webrtc primary; live_webrtc=blocked
- **tech-overview:** systems/people-slice (когда появится)

### 2026-08-12 — TZ004 P6 tech-pause notify @developer

- **Пакеты:** judge_hub + `/ws/judge`, outbox judge.review_* → match.status, overlay rebuild on review
- **Суть:** один review flow → judge UI + overlay banner (/watch); resolve clears banner
- **tech-overview:** systems/platform-api realtime (когда появится)

### 2026-08-12 — TZ004 P5 Agent fake-webrtc @developer

- **Пакеты:** `apps/director-agent` webrtcpub (Pion), `--fake-webrtc`, embedded IVF, README
- **Суть:** publisher offer after peer_joined; signaling reconnect ≠ OBS reconcile; TURN fetch
- **tech-overview:** systems/director-agent-webrtc (когда появится)

### 2026-08-12 — TZ004 P4 /watch subscribe @developer

- **Пакеты:** `apps/overlay` WatchPage + signalingSubscriber + mockStream; nginx `/watch/`
- **Суть:** invite redeem → overlay status + WebRTC recvonly; mock=1 без Agent; max 2 tabs
- **tech-overview:** systems/commentator-watch (когда появится)

### 2026-08-12 — TZ004 P3 signaling + TURN @developer

- **Пакеты:** `docs/WEBRTC-CONTRACT.md`, signaling hub/WS, turn-credentials API, compose coturn profile
- **Суть:** P2P signaling relay (max 2 subs); ephemeral TURN HMAC; auth agent/commentator
- **tech-overview:** systems/webrtc-signaling (когда появится)

### 2026-08-12 — TZ004 P2 judge mobile UI @developer

- **Пакеты:** `apps/judge/` Svelte SPA, nginx `/judge/`, code-map ports
- **Суть:** invite `?token=` → redeem → review/cancel/continue/forfeit; poll status
- **tech-overview:** systems/judge-ui (когда появится)

### 2026-08-12 — TZ004 P1 invites + scoped auth @developer

- **Пакеты:** `apps/api` identity/, invites router, Alembic `0008_invite_tokens`, judge Bearer deps
- **Суть:** opaque invite hash; redeem → session caps; judge API не открытый
- **tech-overview:** systems/platform-api auth (когда появится)

### 2026-08-12 — TZ003 P7 GATE @developer

- **Пакеты:** `scripts/verify.*`, `TZ003-OWNER-SMOKE.md`, ROADMAP этап 2, Failure B pointer
- **Суть:** Production GATE closed на Fake OBS; §5 ТЗ
- **tech-overview:** systems/platform-api + overlay + director-agent (когда появится)

### 2026-08-12 — TZ003 P6 OBS template + Agent docs @developer

- **Пакеты:** `apps/director-agent/templates/`, Agent README bring-up, `overview/code-map.md` ports
- **Суть:** Scene stub + Stream Delay checklist; новый dev поднимает Agent+overlay по README
- **tech-overview:** systems/director-agent (когда появится)

### 2026-08-11 — TZ003 P5 director dashboard @developer

- **Пакеты:** `apps/dashboard/`, `POST .../overlay/override`, nginx `/director/`
- **Суть:** UI сцен/статуса/override только через Platform
- **tech-overview:** systems/dashboard (когда появится)

### 2026-08-11 — TZ003 P4 director-agent Go @developer

- **Пакеты:** `apps/director-agent/` (Go, FakeOBS, OBS WS v5), README
- **Суть:** reconcile desired→actual; A12 restart; e2e fake-obs
- **tech-overview:** systems/director-agent (когда появится)

### 2026-08-11 — TZ003 P3 production API + Agent WS @developer

- **Пакеты:** `apps/api` production PATCH/GET, `/ws/agent/{matchId}`, agent hub, tests
- **Суть:** desired/actual + stub token; fake agent receives desired after PATCH
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ003 P2 overlay Svelte @developer

- **Пакеты:** `apps/overlay/` (Svelte+Vite), `infra/platform/nginx` `/ws/`+`/overlay/`
- **Суть:** Browser Source UI, WS snapshot, watermark STP, build+unit parse
- **tech-overview:** systems/overlay (когда появится)

### 2026-08-11 — TZ003 P1 overlay snapshot/WS @developer

- **Пакеты:** `docs/OVERLAY-CONTRACT.md`, `apps/api` domain overlay/production, alembic `0007`, WS hub, GET overlay, tests
- **Суть:** full overlay.snapshot + version++; Fake score → broadcast; production seed rows
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P5 verify + GATE @developer

- **Пакеты:** `scripts/verify.ps1`, `scripts/verify.sh`, `docs/ROADMAP.md`, `tasks/001_FOUNDATION.md`
- **Суть:** GATE Foundation — verify зелёный, owner smoke, этап 0 отмечен
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P4 layers + outbox @developer

- **Пакеты:** `apps/api/app/{domain,application,infrastructure/outbox,presentation/...}`, probe router, tests
- **Суть:** CreateTournamentDraft в UoW + outbox dispatcher/startup replay + X-Request-ID
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P3 Alembic + /ready @developer

- **Пакеты:** `apps/api/alembic/`, `infrastructure/persistence/`, routers ready, Dockerfile CMD migrate
- **Суть:** таблицы foundation + readiness probe; health без DB
- **tech-overview:** systems/platform-api (когда появится)

### 2026-08-11 — TZ001 P2 compose + env @developer

- **Пакеты:** `infra/platform/docker-compose.yml`, `nginx/`, `apps/api/Dockerfile`, `.env.example`, `overview/code-map.md`
- **Суть:** локальный стек api+mysql+nginx; `/health` через nginx и прямой порт
- **tech-overview:** systems/platform-deploy (когда появится)

### 2026-08-11 — TZ001 P1 monorepo + /health @developer

- **Пакеты:** `apps/api/`, stubs `apps/{overlay,dashboard,judge,director-agent}/`, `infra/{platform,game-server}/`, `packages/api-types/`, `overview/code-map.md`
- **Суть:** каркас monorepo; FastAPI `GET /health` без БД; pytest smoke
- **tech-overview:** systems/platform-api (когда появится)

---

## Формат записи

```markdown
### YYYY-MM-DD — <название> @developer

- **Пакеты:** …
- **Суть:** …
- **tech-overview:** …
```

Не писать: только markdown без кода · секреты · правки только workers/.
