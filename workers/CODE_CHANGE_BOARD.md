# Доска изменений кода (CODE_CHANGE_BOARD)

> **Пишут:** все, кто менял код (developer, devops, …).  
> **Обрабатывает:** scout → `tech-overview/` → архив → очистка.  
> *Scout пока не развёрнут — записи накапливаются до появления роли.*

---

## Ожидают обработки

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
