# Спринт S010

> Оркестратор: [ORCHESTRATOR.md](ORCHESTRATOR.md) · токены: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md)

---

## Активный спринт

| Поле | Значение |
|------|----------|
| **ID** | S010 |
| **Фокус** | TZ010 **gate_ready** (owner smoke); live WHIP/CS2 parallel |
| **Начало** | 2026-08-12 |
| **Цель** | Live комментаторам: OBS WHIP → MediaMTX → WHEP; Fake CI сохранён |

---

## Сейчас открыть вкладки

1. `@owner` — [TZ010-OWNER-SMOKE.md](../developer/notes/TZ010-OWNER-SMOKE.md) → `production_ready=done`
2. `@owner` — [TZ011-OWNER-SMOKE.md](../developer/notes/TZ011-OWNER-SMOKE.md) → `live_whip=done`
3. `@owner` — [TZ009-OWNER-SMOKE.md](../developer/notes/TZ009-OWNER-SMOKE.md) → `live_cs2_local=done` (если ещё open)
4. `team-lead` — Twitch или BestTvGU; коммиты только @owner

---

## Очередь оркестратора

| slug | Задача | Зависит от | Статус |
|------|--------|------------|--------|
| developer | TZ010 Production Ready | P6 gate_ready | **done** (ждёт owner smoke) |
| owner | TZ010-OWNER-SMOKE → production_ready=done | gate_ready | **ready** |
| developer | TZ011 OBS WHIP / MediaMTX | P6 gate_ready | **done** (ждёт owner smoke) |
| owner | TZ011-OWNER-SMOKE → live_whip=done | gate_ready | **ready** |
| owner | TZ009-OWNER-SMOKE → live_cs2_local=done | gate_ready | **ready** |
| owner | TZ007 Alpha Fake smoke (если open) | — | ready |
| team-lead | После live_whip / live_cs2_local: Twitch или TZ010 | owner smoke | pending |
| devops | VPS CS2 / MediaMTX ICE только по запросу | owner | pending |

---

## Журнал (новые сверху)

```text
2026-08-12 developer: Admin UI simplify — action-first; mobile stepper; MatchOps compact; build OK
2026-08-12 developer: TZ010 P6 gate_ready — VERIFY OK Fake; @owner TZ010-OWNER-SMOKE → production_ready=done; TL Twitch/BestTvGU
2026-08-12 developer: TZ010 P5 done — OWNER-SMOKE draft + 2nd tournament checklist; дальше P6 verify/GATE (новый чат)
2026-08-12 developer: TZ010 P4 done — docs/UPDATE.md (git pull/migrate/profiles); дальше P5 second tournament (новый чат)
2026-08-12 developer: TZ010 P3 done — PRODUCTION-RECOVERY; Failure B = Go+pointer; pytest A–E OK; дальше P4 update (новый чат)
2026-08-12 developer: TZ010 P2 done — PRODUCTION-RUNBOOK hub; дальше P3 recovery (новый чат)
2026-08-12 developer: TZ010 P1 done — RECON: hub missing; Failure B already in Go; дальше P2 PRODUCTION-RUNBOOK (новый чат)
2026-08-12 developer: TZ011 P6 gate_ready — VERIFY OK Fake; OWNER-SMOKE ready; @owner → live_whip=done; TL Twitch/TZ010
2026-08-12 developer: TZ011 P5 done — live_whip docs/scripts; no --live-webrtc default; OWNER-SMOKE draft; дальше P6 verify/GATE (новый чат)
2026-08-12 developer: TZ011 P4 done — /watch WHEP default + fake/mock; waiting WHIP UX; дальше P5 docs (новый чат)
2026-08-12 developer: TZ011 P3 done — whip-publish/whep-play + mediamtx-auth; max2=429; tests OK; дальше P4 /watch WHEP (новый чат)
2026-08-12 developer: TZ011 P2 done — ADR-037 + WEBRTC-CONTRACT protocol 1/2; дальше P3 credentials API (новый чат)
2026-08-12 developer: TZ011 P1 done — MediaMTX whip profile + WHEP lab OK; ADR-037 draft; SPIKE WHIP∥Twitch=dual-output; дальше P2 новый чат
2026-08-12 developer: TZ009 P6 gate_ready — OWNER-SMOKE ready; DS down; @owner → live_cs2_local=done; TL Twitch/TZ010
2026-08-12 developer: TZ009 P5 done — VERIFY OK Fake (TZ009 banner; no CS2 DS); дальше P6 OWNER-SMOKE/GATE
2026-08-12 developer: TZ009 P4 done — OWNER-SMOKE draft + LOCAL-CS2/ALPHA-LIVE/organizer; дальше P5 verify
2026-08-12 developer: TZ009 P3 done — start-live + MatchOps; Fake /start OK; дальше P4 docs/smoke draft
2026-08-12 developer: TZ009 P2 done — Bridge 0.2.0 CSS round_*/score → Platform; DLL on DS; owner restart for live smoke; дальше P3
2026-08-12 developer: TZ009 P1 done — RECON gaps + GATE events (heartbeat+round_end); дальше P2 Bridge hooks
2026-08-12 team-lead/dev: S010 — TZ009 Live CS2 Local runbook M=6; Production Ready → TZ010; developer ready P1
2026-08-12 owner: live blockers lifted — live_obs=done; live_cs2_local/live_twitch=ready; пробный матч @owner
2026-08-12 owner/dev: TZ008 GATE closed — live_webrtc=done; real OBS+RTC; encode bump 1080p/3500k; next TZ009
2026-08-12 developer: TZ008 P5 done — OWNER-SMOKE; VERIFY OK; gate_ready; VCam OK; /watch ждёт @owner (Docker down)
2026-08-12 developer: TZ008 P4 done — VERIFY OK TZ008 Fake CI; live_track unit; дальше P5 OWNER-SMOKE
2026-08-12 developer: TZ008 P3 done — director.md + Agent §4c Live Virtual Cam + ALPHA-LIVE-TRACKS; дальше P4
2026-08-12 developer: TZ008 P2 done — LiveTrack FFmpeg dshow→VP8→Pion; --live-webrtc; go test OK; дальше P3
2026-08-12 developer: TZ008 P1 done — WEBRTC-CONTRACT Live + spike OBS Virtual Camera; дальше P2
2026-08-12 team-lead/dev: S009 — TZ008 Live WebRTC runbook M=5; Production Ready → TZ009
```
