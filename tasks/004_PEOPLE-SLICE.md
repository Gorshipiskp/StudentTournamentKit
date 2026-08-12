# ТЗ 004 — People Slice (судья + комментаторы)

| Поле | Значение |
|------|----------|
| **Статус** | **done** (GATE 2026-08-12; `live_webrtc=done` via TZ008) |
| **Owner** | @team-lead / @owner |
| **Исполнитель** | developer (+ devops coturn при блокере) |
| **Этап roadmap** | 3 — People Slice |
| **Предыдущий** | TZ003 Production Slice (GATE done) |
| **Следующий** | TZ005 Tournament Slice |

---

## 0. Цель (для людей)

Судья с телефона ведёт проверку/паузу/техпоражение. Один–два комментатора **удалённо** открывают ссылку в браузере и видят **live** картинку production (WebRTC), плюс статус техпаузы — без доступа к OBS режиссёра.

---

## 1. Scope

**В scope:**

- Invite links: роли `judge` / `commentator` (opaque token, scope match/tournament, TTL, revoke)
- Auth: invite → session; capability checks на API/WS subscribe
- `apps/judge/` — mobile-first UI на существующий judge API (review-request / cancel / resolve)
- Commentator viewer: route `/watch/[token]` (в `apps/overlay` или отдельный entry) — WebRTC player + match status
- Platform: WebRTC **signaling** (offer/answer/ICE) через WS; short-lived TURN credentials
- `coturn` в `infra/platform/docker-compose` (profile `webrtc` допустим)
- Director Agent: WebRTC **publisher** (OBS Virtual Cam → encode → Pion) **или** Fake publisher для primary GATE без камеры
- Уведомления tech pause / review: judge UI + commentator UI + уже существующий overlay banner
- Расширить `scripts/verify.ps1`
- Owner smoke primary без живого CS2 (Fake match + Fake/optional real WebRTC)

**Вне scope:**

- Аудио комментаторов в платформе (Voicemeeter → OBS — вне STK)
- SFU / LiveKit / mediasoup
- Полный tournament admin / branding wizard (→ Tournament Slice)
- Live CS2 VPS как обязательный GATE
- OBS Stream Delay automation
- BestTvGU

**Уже есть (переиспользовать):**

- Judge API: `POST .../judge/review-request|cancel|resolve`
- Overlay snapshot + judge banner
- Director Agent + Fake OBS (TZ003)
- Fake CS2 match flow (TZ002)

---

## 2. Frozen (не менять без TL)

- **F1:** Видео комментаторам с **ноутбука режиссёра** (Agent), не с Platform VPS media relay (VISION / ADR-008)
- **F2:** Browser-only WebRTC; 1–2 viewers; P2P + TURN, без SFU (ADR-022)
- **F3:** Agent — sole OBS authority; dashboard не говорит с OBS (A8)
- **F4:** Invite tokens: random ≥32 bytes, store hash, scoped caps, revoke (ADR identity)
- **F5:** Overlay = full snapshot; production desired/actual (ADR-030, A12)
- **F6:** Single API replica; no Redis (ADR-031)
- **F7:** Audio WebRTC **выкл** в v1 (operational assumption)
- **F8:** Секреты в `.env`; коммиты только @owner
- **F9:** A1–A12

---

## 3. To-be / UX

1. Организатор (или director API) создаёт invite judge + commentator
2. Судья открывает ссылку на телефоне → видит статус матча → «Запрос проверки» → пауза → continue/forfeit
3. Комментатор открывает `/watch/...` → видит video (Fake или Agent) + баннер техпаузы
4. При Agent restart — signaling/reconnect; desired production не ломается (TZ003)

---

## 4. Техника

| Слой | Пути |
|------|------|
| Invites / auth | `apps/api/.../identity`, routers invites |
| Judge UI | `apps/judge/` (SvelteKit или Svelte SPA mobile) |
| Watch / WebRTC | `apps/overlay` route `/watch` или `apps/overlay` + shared |
| Signaling | Platform WS channel `match:{id}:commentator` / agent |
| TURN | `infra/platform` coturn + API credentials endpoint |
| Publisher | `apps/director-agent` webrtc package + `--fake-webrtc` |
| Docs | `docs/WEBRTC-CONTRACT.md` (короткий) |

---

## 5. Приёмка

### Primary GATE (обязательно)

- [x] Invite create/revoke для judge + commentator
- [x] Judge mobile UI: полный review flow на Fake match
- [x] Commentator `/watch`: получает status + WebRTC media (Fake publisher допустим)
- [x] Tech pause виден у судьи и комментатора
- [x] Signaling reconnect после краткого disconnect
- [x] coturn в compose (или documented profile) + credentials API
- [x] `verify.ps1` зелёный
- [x] Owner smoke ≤ 20 мин (инструкция в notes)

### Optional live

- [x] Agent publisher с OBS Virtual Cam → `/watch` — **TZ008 done** ([008_LIVE-WEBRTC.md](008_LIVE-WEBRTC.md))
- [x] Статус: `live_webrtc=done` (2026-08-12 @owner)

---

## 6. Runbook

- `workers/developer/notes/TZ004-PROMPT-RUNBOOK.md`
- `workers/developer/notes/TZ004-NEW-CHAT.md`
- Промптов: **M = 7** (P7 = GATE)

---

## 7. Паритет

Judge — mobile web; commentator — desktop/mobile browser. Один backend API.

---

## Контекст

- TZ002 judge API + Fake CS2
- TZ003 overlay + Agent + dashboard
- [docs/INVARIANTS.md](../docs/INVARIANTS.md), [docs/TECH-STACK.md](../docs/TECH-STACK.md) § WebRTC
- [docs/DECISIONS.md](../docs/DECISIONS.md) ADR-008, 022, 031
