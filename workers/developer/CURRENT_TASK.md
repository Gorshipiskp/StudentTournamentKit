# CURRENT_TASK

| Поле | Значение |
|------|----------|
| **ID** | TZ005 |
| **От** | @team-lead |
| **Статус** | **done** (GATE 2026-08-12) |
| **Исполнитель** | workers/developer/ |

## Цель

Tournament Slice: organizer admin, teams, bracket, branding, invites из UI — GATE по tasks/005_TOURNAMENT-SLICE.md.

## Scope

**Делать:** P1…P7 по `workers/developer/notes/TZ005-PROMPT-RUNBOOK.md` (1 чат = 1 промпт)

**Не трогать:** Broadcast delay; BestTvGU; auto-seeding; коммиты без @owner

## Критерии готовности

- [x] Трекер P1–P7 done
- [x] §5 Primary GATE
- [x] Owner smoke (инструкция + verify)

## Контекст

- `tasks/005_TOURNAMENT-SLICE.md`
- `workers/developer/notes/TZ005-PROMPT-RUNBOOK.md`
- TZ002–004: matches, overlay, invites, dashboard director

## Журнал задачи

| Дата | Запись |
|------|--------|
| 2026-08-12 | **GATE closed** — verify OK TZ005; OWNER-SMOKE; live_cs2/live_webrtc=blocked; next TZ006 |
| 2026-08-12 | P6 done — wizard + multi-tournament smoke; следующий P7 GATE |
| 2026-08-12 | P5 done — Fake start + staff links; следующий P6 polish |
| 2026-08-12 | P4 done — branding → overlay; следующий P5 invites/start |
| 2026-08-12 | P3 done — bracket generate/assign + match_id; следующий P4 branding |
| 2026-08-12 | P2 done — teams/players API + UI; следующий P3 bracket |
| 2026-08-12 | P1 done — auth + tournament CRUD + `/admin`; следующий P2 teams |
