# TZ004 — PROMPT RUNBOOK · People Slice

> ТЗ: [tasks/004_PEOPLE-SLICE.md](../../../tasks/004_PEOPLE-SLICE.md)  
> База: TZ001–003 (Foundation + Game + Production GATE)  
> **M = 7** · P7 = GATE · 1 чат = 1 промпт

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/7 | Invites + scoped auth (judge/commentator) | **done** | 2026-08-12 |
| 2/7 | Judge mobile UI → existing API | **done** | 2026-08-12 |
| 3/7 | Signaling WS + TURN credentials + coturn | **done** | 2026-08-12 |
| 4/7 | Commentator `/watch` + WebRTC subscribe | **done** | 2026-08-12 |
| 5/7 | Agent WebRTC publisher (или `--fake-webrtc`) | **done** | 2026-08-12 |
| 6/7 | Tech-pause notify (judge + watch + overlay) | **done** | 2026-08-12 |
| 7/7 | verify + OWNER-SMOKE + GATE | **done** | 2026-08-12 |

**GATE:** closed · `live_webrtc=blocked` · Owner smoke: `TZ004-OWNER-SMOKE.md`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/7 | §0 · §1 invites · §2 F4 · §4 |
| 2/7 | §1 judge UI · TZ002 judge endpoints |
| 3/7 | §1 signaling/TURN · §2 F2 F6 · TECH-STACK coturn |
| 4/7 | §1 watch · §2 F1 F2 F7 · WEBRTC contract |
| 5/7 | §1 Agent publisher · §2 F1 F3 · ADR-008/021 |
| 6/7 | §1 notifications · overlay judge banner |
| 7/7 | §3 · §5 Приёмка |

---

## P1/7 — Invites + scoped auth

### Делать

- Модель `invite_tokens` (если ещё нет полной): hash, role, match_id, expires_at, revoked_at
- API: создать invite (organizer/director), revoke, redeem → session/JWT short-lived
- Capabilities: `judge.review`, `judge.resolve`, `overlay.read` / `commentator.watch`
- Проверка scope на match endpoints и будущих WS subscribe
- Тесты: redeem, revoke, expired, wrong match

### Не делать

- UI судьи (P2)
- WebRTC (P3+)
- Публичная регистрация пользователей

### DoD

- [x] Create/redeem/revoke работают
- [x] Judge API принимает invite-session (не только «открытый» доступ)
- [x] Pytest зелёный

---

## P2/7 — Judge mobile UI

### Делать

- `apps/judge/`: mobile-first Svelte (Kit или SPA)
- Экраны: статус матча, «Запрос проверки», «Отменить», «Продолжить», «Тех. поражение»
- Крупные кнопки, мало кликов; RU copy
- Auth через invite token в URL/query
- Подписка на статус (WS или polling) — tech pause / review_status
- README + dev script

### Не делать

- WebRTC viewer
- Desktop dashboard redesign
- Новые judge semantics (API уже есть)

### DoD

- [x] На Fake match полный review→pause→continue и forfeit с телефона/devtools mobile
- [x] Без invite — отказ
- [ ] Build проходит в verify (позже P7)

---

## P3/7 — Signaling + TURN + coturn

### Делать

- Короткий `docs/WEBRTC-CONTRACT.md`: signaling messages, roles, protocol version
- Platform WS: relay offer/answer/ICE между Agent (publisher) и commentator (subscriber)
- API: ephemeral TURN credentials (TTL short)
- Compose: `coturn` service (profile `webrtc` ok) + README
- Auth: только invite commentator / agent session на signaling channel

### Не делать

- Полный media path (P4–P5)
- SFU

### DoD

- [x] Два test peer (или unit) обмениваются signaling через Platform
- [x] TURN credentials выдаются и истекают
- [x] Compose config валиден с coturn profile

---

## P4/7 — Commentator `/watch` + subscribe

### Делать

- UI `/watch/[token]`: `<video>`, status strip (score optional, tech pause banner)
- WebRTC subscriber (browser RTCPeerConnection)
- Redeem invite → connect signaling → wait for offer/answer
- Graceful: нет publisher → понятное «ожидание эфира»
- Переиспользовать overlay snapshot WS для status **или** dedicated commentator channel

### Не делать

- Audio tracks (F7)
- Agent capture (P5) — можно мок RTCPeerConnection loopback для UI test

### DoD

- [x] С Fake signaling peer страница показывает remote stream (или mock)
- [x] Tech pause banner обновляется
- [x] 1–2 вкладки `/watch` поддерживаются архитектурно (документировать лимит)

---

## P5/7 — Agent WebRTC publisher

### Делать

- В `apps/director-agent`: publisher path
  - Primary GATE: `--fake-webrtc` (synthetic frames / test pattern) → Pion
  - Optional: OBS Virtual Cam → FFmpeg → Pion (documented; не обязателен для GATE)
- Connect to Platform as agent; answer commentator offers (или reverse: agent offers — зафиксировать в CONTRACT)
- Reconnect: новый signaling, не ломая OBS reconcile (TZ003)
- README: ports, flags, NAT/TURN

### Не делать

- FFmpeg Twitch delay (ADR-024)
- Audio mix

### DoD

- [x] `--fake-webrtc` + `/watch` → video виден в браузере (localhost)
- [x] Agent restart → commentator может переподключиться (smoke)
- [x] Whitelist: не произвольный OBS execute

---

## P6/7 — Tech-pause notifications

### Делать

- При review_requested / tech_pause / resolve:
  - push в judge WS/UI
  - push в commentator status
  - overlay banner уже из merge — проверить end-to-end
- Не дублировать бизнес-логику — подписаться на outbox/events
- Тесты на уведомления (хотя бы API-level)

### Не делать

- Новые judge outcomes
- Discord integration

### DoD

- [x] Один review flow обновляет judge + watch + overlay согласованно
- [x] Нет рассинхрона статусов после resolve

---

## P7/7 — verify + GATE

### Делать

- `scripts/verify.ps1`: api tests + judge/overlay build + agent tests + fake-webrtc smoke если есть
- `workers/developer/notes/TZ004-OWNER-SMOKE.md`
- ROADMAP § People checklist; CURRENT; WORKLOG
- Явно: `live_webrtc=blocked|done`

### Не делать

- Tournament Slice
- Scope creep

### DoD (GATE)

- [x] §5 Primary GATE
- [x] Owner smoke проходим по инструкции
- [x] Трекер P1–P7 done

### Owner smoke (primary)

```text
1. compose up (+ webrtc profile)
2. Fake CS2 match + assign (как TZ002)
3. Agent: fake-obs + fake-webrtc
4. Создать invites judge + commentator
5. Judge UI: review → pause → continue
6. /watch: video + баннер паузы
7. verify.ps1
```

---

## Эскалация

| Ситуация | Куда |
|----------|------|
| coturn/NAT ад ад | Fake-webrtc localhost GATE; live_webrtc=blocked |
| Нет камеры/OBS | `--fake-webrtc` обязателен для GATE |
| Conflict Frozen | @team-lead |

---

## После GATE

→ **TZ005 Tournament Slice** (admin wizard, bracket UI, multi-tournament, branding).
