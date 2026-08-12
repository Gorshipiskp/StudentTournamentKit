# TZ006 — PROMPT RUNBOOK · Broadcast Slice

> ТЗ: [tasks/006_BROADCAST-SLICE.md](../../../tasks/006_BROADCAST-SLICE.md)  
> База: TZ001–005 GATE (Foundation → Tournament; live optional)  
> **M = 7** · P7 = GATE · 1 чат = 1 промпт  
> Философия: вертикали · ADR-024 OBS delay v1 · без FFmpeg в Agent

---

## Трекер

| P | Цель | Статус | Чат / дата |
|---|------|--------|------------|
| 1/7 | Broadcast contract + delay checklist (director UI) | pending | |
| 2/7 | Overlay scene polish (6 layouts + branding) | pending | |
| 3/7 | match_audit_log persistence + writers | pending | |
| 4/7 | Match health aggregate API | pending | |
| 5/7 | Director: health panel + delay widget | pending | |
| 6/7 | Audit log UI (director match) | pending | |
| 7/7 | verify + OWNER-SMOKE + GATE | pending | |

Статусы: `pending` · `running` · `done` · `blocked`

---

## Карта промптов → § ТЗ

| P | Читать |
|---|--------|
| 1/7 | §0 · §1 delay · §2 F1 F7 · ADR-024 · director-agent/templates README §3 |
| 2/7 | §1 overlay polish · §2 F4 F5 · OVERLAY-CONTRACT · scenes.json |
| 3/7 | §1 audit · §2 F6 · ARCHITECTURE match_audit_log |
| 4/7 | §1 health · INVARIANTS production/broadcast · TZ003 production API |
| 5/7 | §3 UX director · §4 |
| 6/7 | §3 audit UI · P3 API |
| 7/7 | §3 · §5 Приёмка |

---

## P1/7 — Broadcast contract + delay checklist

### Делать

- Короткий `docs/BROADCAST-DELAY.md`: OBS Stream Delay v1, ссылка ADR-024, что Agent **не** автоматизирует
- Director `/director/:matchId`: блок «Задержка Twitch» — значение из tournament `configured_broadcast_delay_seconds` + чек-лист (RU, глаголы)
- Ссылка на `apps/director-agent/templates/README.md` § Stream Delay
- Без изменения OBS через API

### Не делать

- FFmpeg в Agent
- Overlay redesign (P2)
- Audit/health (P3–P6)

### DoD

- [ ] Director показывает delay hint турнира + checklist
- [ ] Документ в репо

### После P

- WORKLOG; трекер P1=done; новый чат P2

---

## P2/7 — Overlay scene polish

### Делать

- `apps/overlay/`: отдельные layout-компоненты или ветки по `snapshot.scene` для waiting/intro/teams/ingame/break/winner
- Branding TZ005 (logo/colors) + счёт/команды на ingame; intro/teams/winner — названия команд, турнир
- Watermark STK сохранить
- `npm run build` overlay; smoke README URL

### Не делать

- Health/audit
- Новые scene names вне `scenes.json`
- Twitch integration

### DoD

- [ ] Все 6 сцен рендерятся без пустых заглушек
- [ ] Build OK; watermark виден

### После P

- WORKLOG; P2=done; новый чат P3

---

## P3/7 — Audit log backend

### Делать

- Alembic: `match_audit_log` (поля по ARCHITECTURE §8.2)
- Application helper: `write_audit(match_id, actor, action, payload, correlation_id)`
- Подключить к существующим путям: judge review/resolve, production scene change, match start (organizer/director), значимые system events (минимум 5 action types)
- `GET /api/v1/matches/{id}/audit?limit=50` (director/organizer auth)
- Pytest

### Не делать

- UI (P6)
- Публичный audit API

### DoD

- [ ] Запись при smoke flow; GET возвращает sorted list
- [ ] correlation_id прокидывается где уже есть

### После P

- WORKLOG; P3=done; новый чат P4

---

## P4/7 — Match health aggregate API

### Делать

- `GET /api/v1/matches/{id}/health` (или расширить production): platform ok, agent_status, obs_status, overlay revision/age, game_server heartbeat (Fake ok), broadcast_status stub
- Семантика degraded/ok/offline по INVARIANTS (не выдумывать новые enum без нужды)
- Pytest с Fake production session

### Не делать

- Full monitoring stack / Prometheus
- Director UI (P5)

### DoD

- [ ] Endpoint отражает состояние после Fake OBS connect
- [ ] 404/401 корректны

### После P

- WORKLOG; P4=done; новый чат P5

---

## P5/7 — Director health + delay widget

### Делать

- Director page: health panel (poll или WS match health) — цвет/иконка по компонентам
- Интеграция P1 delay checklist + P4 health в одном экране
- RU copy; пустые состояния (agent offline — понятное сообщение)
- Не ломать scene buttons / overrides

### Не делать

- Audit UI (P6)
- Admin global health

### DoD

- [ ] Fake OBS: agent+obs зелёные/connected в UI
- [ ] Delay block + health на одной странице

### После P

- WORKLOG; P5=done; новый чат P6

---

## P6/7 — Audit log UI

### Делать

- Director (или вкладка на match): список audit entries — время, актор, действие, краткий результат (RU labels)
- Auto-refresh после scene/judge actions
- Короткий `docs/BROADCAST-HEALTH.md` или § в dashboard README

### Не делать

- Export CSV
- Фильтры beyond limit=50

### DoD

- [ ] После смены сцены + judge action записи видны в UI
- [ ] README обновлён

### После P

- WORKLOG; P6=done; новый чат P7

---

## P7/7 — verify + OWNER-SMOKE + GATE

### Делать

- `scripts/verify.ps1` шаги TZ006
- `workers/developer/notes/TZ006-OWNER-SMOKE.md` (≤25 мин, Fake OBS)
- Пройти §5 Primary GATE; обновить ТЗ чеклисты
- Трекер all done; CURRENT; WORKLOG; CODE_CHANGE_BOARD; ROADMAP этап 5
- `live_twitch=blocked` если owner не гонял реальный Twitch

### Не делать

- FFmpeg delay
- Scope Tournament Alpha

### DoD

- [ ] verify зелёный
- [ ] OWNER-SMOKE написан; GATE closed

### После P

- Следующая волна: TZ007 Tournament Alpha (TL)

---

## Однострочник владельца (P2+)

```text
Очередь: workers/sprint/CURRENT.md — developer. Промпт N/7 из TZ006-PROMPT-RUNBOOK.md. Выполни, обнови статус и журнал.
```
