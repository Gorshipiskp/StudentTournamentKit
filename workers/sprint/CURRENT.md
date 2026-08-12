# Спринт S006

> Оркестратор: [ORCHESTRATOR.md](ORCHESTRATOR.md) · токены: [TOKEN-HYGIENE.md](../TOKEN-HYGIENE.md)

---

## Активный спринт

| Поле | Значение |
|------|----------|
| **ID** | S006 |
| **Фокус** | TZ005 Tournament GATE closed → ждём TL на TZ006 Broadcast |
| **Начало** | 2026-08-12 |
| **Цель** | Primary GATE: нетехник создаёт турнир и запускает Fake-матч из UI — **достигнута** |

---

## Сейчас открыть вкладки

1. `team-lead` — закрыть S006 / открыть TZ006 Broadcast Slice
2. `tester` — optional owner smoke по `TZ005-OWNER-SMOKE.md`

---

## Очередь оркестратора

| slug | Задача | Зависит от | Статус |
|------|--------|------------|--------|
| team-lead | Закрыть TZ005/S006; открыть TZ006 | — | ready |
| developer | TZ005 P1…P7 Tournament GATE | team-lead | done |
| tester | Owner smoke после GATE | developer GATE | ready |
| devops | только при блокере env/compose | developer | pending |

---

## Журнал (новые сверху)

```text
2026-08-12 developer: TZ005 GATE closed — verify OK; OWNER-SMOKE; next TZ006 Broadcast
2026-08-12 developer: TZ005 P6 done — wizard UX + multi-tournament smoke; next P7 GATE
2026-08-12 developer: TZ005 P5 done — Fake start + staff invite links from admin
2026-08-12 developer: TZ005 P4 done — branding BLOBs → overlay logo/colors
2026-08-12 developer: TZ005 P3 done — single-elim bracket + match link
2026-08-12 developer: TZ005 P2 done — teams/players API + /admin/tournaments/{id}
2026-08-12 developer: TZ005 P1 done — organizer auth + tournament CRUD + /admin
2026-08-12 team-lead: S006 — TZ004 closed; TZ005 Tournament Slice runbook M=7; developer ready P1
2026-08-12 developer: TZ004 GATE closed — verify OK; live_webrtc=blocked; OWNER-SMOKE ready
2026-08-12 developer: TZ004 P1–P6 done (invites→judge→signaling→watch→Agent fake-webrtc→notify)
2026-08-12 team-lead: S005 — TZ003 closed; TZ004 People Slice runbook M=7
2026-08-12 developer: TZ003 GATE done — Fake OBS; Failure B closed
2026-08-11 team-lead: TZ002 primary GATE (live_smoke=blocked без VPS)
```

---

*Журнал: max 60 записей → sprint/archive/*
