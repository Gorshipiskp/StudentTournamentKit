# Контракт CS2 ↔ Platform

> Канон для Fake (`tools/fake-cs2/`) и живого `STP.Bridge`.  
> Согласовано с [INVARIANTS §6](../../docs/INVARIANTS.md), [ARCHITECTURE §11](../../docs/ARCHITECTURE.md).  
> Domain **не** содержит типов MatchZy/RCON — только нормализованные события и whitelist-команды (A4, A7).

**protocol_version:** `1`

---

## 1. Направление потоков

```text
CS2 / Fake ──POST events (+HMAC)──► Platform  POST /api/v1/internal/cs2/events
Platform    ──POST commands──────► CS2 / Fake  (HTTP на game endpoint)
CS2 / Fake  ──ack (в ответе)─────► Platform    (HTTP 200 ≠ applied; нужен ack)
```

Events = быстрый путь. Snapshot = восстановление. Reconciliation = корректность.

---

## 2. HMAC (webhooks)

Подпись тела запроса (raw bytes, UTF-8 JSON без лишних пробелов — как отправлено):

| Header | Значение |
|--------|----------|
| `X-STP-Signature` | `sha256=` + hex(`HMAC-SHA256(webhook_secret, raw_body)`) |
| `X-STP-Event-Id` | тот же `event_id`, что в JSON (удобство логирования) |
| `Content-Type` | `application/json` |
| `X-STP-Protocol-Version` | `1` (опционально, рекомендуется) |

Пример:

```text
X-STP-Signature: sha256=a1b2c3…
X-STP-Event-Id: 550e8400-e29b-41d4-a716-446655440000
```

Секрет — per `game_servers.webhook_secret` (или env Fake). Не логировать секрет.

---

## 3. Events (CS2 → Platform)

### Endpoint

`POST /api/v1/internal/cs2/events`

(до P2 ingest может отвечать 404 — Fake всё равно шлёт на этот URL; см. README Fake.)

### Обязательные поля тела

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "sequence": 183,
  "server_id": "srv_abc",
  "match_id": "m_xyz",
  "type": "round_end",
  "timestamp": "2026-08-11T16:00:00Z",
  "correlation_id": "corr_optional",
  "payload": {}
}
```

| Поле | Правила |
|------|---------|
| `event_id` | UUID; UNIQUE в той же транзакции, что update match (transport dedup) |
| `sequence` | Целое ≥ 1; монотонно **per match** (gap / OOO → reconcile, не молча перетирать) |
| `server_id` | ID зарегистрированного game server |
| `match_id` | ID матча на Platform |
| `type` | Нормализованный тип (таблица ниже) |
| `timestamp` | ISO-8601 UTC |
| `correlation_id` | Опционально; прокидывать сквозь цепочку |
| `payload` | Объект; зависит от `type` |

### Типы событий (whitelist v1)

| `type` | Когда | Ключ в `payload` |
|--------|-------|------------------|
| `match_loaded` | Матч загружен на сервере | `map` |
| `round_start` | Старт раунда (в т.ч. buy) | `round`, `phase` (`buy` \| `live` \| …) |
| `round_end` | Конец раунда + счёт | `round`, `score` `{ "team_a", "team_b" }`, `map` |
| `score_changed` | Явное обновление счёта (если не в `round_end`) | `score`, `round` |
| `tech_pause_started` | Фактическая тех. пауза | `reason` (опц.) |
| `tech_pause_ended` | Пауза снята | — |
| `match_completed` | Матч окончен на сервере | `score`, `reason` (`normal` \| `forfeit` \| …) |
| `heartbeat` | Периодический пульс Bridge/Fake | `bridge_version`, `protocol_version` |

Handlers на Platform — идемпотентны: `apply(e); apply(e)` безопасно.

---

## 4. Commands (Platform → CS2)

### Endpoint Fake / Bridge

`POST /v1/commands` на HTTP-слушателе игрового контура (Fake: порт из конфига).

### Тело команды

```json
{
  "command_id": "660e8400-e29b-41d4-a716-446655440001",
  "type": "PauseMatch",
  "match_id": "m_xyz",
  "server_id": "srv_abc",
  "timestamp": "2026-08-11T16:01:00Z",
  "correlation_id": "corr_optional",
  "payload": {}
}
```

### Whitelist `type`

| Команда | Назначение | `payload` |
|---------|------------|-----------|
| `LoadMatch` | Загрузить матч | `map`, опц. настройки |
| `PauseMatch` | Тех. пауза | опц. `reason` |
| `ResumeMatch` | Снять паузу | — |
| `ForfeitMatch` | Тех. поражение | `losing_team`: `team_a` \| `team_b` |
| `GetSnapshot` | Snapshot для reconcile | — |

Сырой RCON из application layer **запрещён**.

### Ack (ответ HTTP)

HTTP 200 на доставку ≠ команда применена. Успех — поле `status` в ack:

```json
{
  "command_id": "660e8400-e29b-41d4-a716-446655440001",
  "type": "PauseMatch",
  "status": "confirmed",
  "timestamp": "2026-08-11T16:01:00.120Z",
  "error": null,
  "result": null
}
```

| `status` | Смысл |
|----------|--------|
| `accepted` | Принято в очередь (ещё не applied) |
| `confirmed` | Applied; actual обновлён (и/или уйдёт event) |
| `failed` | Отказ; смотреть `error` |
| `duplicate` | Тот же `command_id` уже обработан — вернуть прежний исход |

Для `GetSnapshot` при `confirmed`:

```json
{
  "command_id": "…",
  "type": "GetSnapshot",
  "status": "confirmed",
  "timestamp": "…",
  "error": null,
  "result": { "snapshot": { } }
}
```

Повтор того же `command_id` — идемпотентен (тот же исход, без повторного side effect).

Жизненный цикл на Platform (P3+): `requested → sent → confirmed | failed`.

---

## 5. Snapshot

Обязателен для recovery / reconcile (heartbeat, restart, sequence gap).

```json
{
  "match_id": "m_xyz",
  "server_id": "srv_abc",
  "map": "de_mirage",
  "round": 12,
  "score": { "team_a": 7, "team_b": 5 },
  "phase": "freeze",
  "paused": false,
  "loaded": true,
  "completed": false,
  "last_sequence": 183,
  "players": []
}
```

| Поле | Смысл |
|------|-------|
| `phase` | Нормализованная фаза: `warmup` \| `buy` \| `live` \| `freeze` \| `overtime` \| `ended` |
| `paused` | **Actual** pause на сервере |
| `last_sequence` | Последний отправленный `sequence` event |
| `players` | v1 может быть `[]`; формат расширится позже |

Также: `GET /v1/snapshot` на Fake (удобство без command_id) — тот же JSON.

---

## 6. Sequence и идемпотентность (кратко)

1. Fake/Bridge инкрементирует `sequence` per match при каждом исходящем event.
2. Platform хранит `last_sequence`; gap или out-of-order → флаг reconcile / `GetSnapshot`, не silent overwrite истории.
3. Дубликат `event_id` → 200 no-op (после появления ingest).
4. Desired pause на Platform ≠ actual, пока нет ack / event `tech_pause_*`.

---

## 7. Health Fake

`GET /health` → `{"status":"ok","role":"fake-cs2","protocol_version":"1",…}`

---

## Связанные пути

| Артефакт | Путь |
|----------|------|
| Fake Game Server | `tools/fake-cs2/` |
| Ingest (P2) | `POST /api/v1/internal/cs2/events` |
| Bridge (P6) | `infra/game-server/plugins/STP.Bridge/` |
| Инварианты | `docs/INVARIANTS.md` §6 |
| Архитектура | `docs/ARCHITECTURE.md` §11, §15.3 |
