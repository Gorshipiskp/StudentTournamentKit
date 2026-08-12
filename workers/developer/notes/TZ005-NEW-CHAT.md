# TZ005 — NEW CHAT · копипаст

> 1 чат = 1 промпт. Ниже — **P1/7**.  
> Ранбук: [TZ005-PROMPT-RUNBOOK.md](TZ005-PROMPT-RUNBOOK.md) · ТЗ: [tasks/005_TOURNAMENT-SLICE.md](../../../tasks/005_TOURNAMENT-SLICE.md)

---

## P1/7 (вставить в новый чат Developer)

```text
Проект: BestCSTournaments (StudentTournamentKit).

Роль: Developer · workers/developer/.
Онбординг: L1 — product § · code-map § · IDENTITY · WORKLOG · ARCHITECTURE §8–9 (tournaments/auth).
База: TZ001–004 GATE в репо (matches, overlay, invites, dashboard director).

ТЗ: tasks/005_TOURNAMENT-SLICE.md — §0 · §1 (auth/tournaments) · §2 Frozen · §4.
Промпт 1/7 — Organizer auth + tournament CRUD (API + /admin list).

Делать:
- Login организатора инстанса (env bootstrap → JWT/session)
- Расширить tournaments (name, format, settings_json, status draft|published|completed)
- API list/create/get/patch/publish; 401 без auth
- apps/dashboard /admin: login + список + создать draft
- Alembic + pytest; не ломать Fake matches / director page

Не делать: teams/bracket/branding/invites UI (P2–P5); multi-user RBAC; коммит без @owner.

DoD: login → список → create → publish; pytest OK; director без регрессии.

После: WORKLOG; трекер P1=done в TZ005-PROMPT-RUNBOOK.md; стоп — P2 в новом чате.
```

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/7 из TZ005-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```

---

## После всей волны

Owner smoke: `TZ005-OWNER-SMOKE.md` (появится на P7).  
Далее: **TZ006 Broadcast Slice**.
