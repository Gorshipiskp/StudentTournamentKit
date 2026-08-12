# Broadcast Delay — контракт v1

> Публичный Twitch идёт с задержкой; комментаторы смотрят live.  
> Решение: [DECISIONS.md](DECISIONS.md) **ADR-024**.  
> Чек-лист OBS: [apps/director-agent/templates/README.md](../apps/director-agent/templates/README.md) §3.

---

## Смысл

| Поток | Задержка | Кто смотрит |
|-------|----------|-------------|
| Twitch (RTMP из OBS) | **OBS Stream Delay** (~90–120 с, как в турнире) | Зрители |
| Live WebRTC | **без** delay | Комментаторы (TZ004) |

Параметр турнира `configured_broadcast_delay_seconds` — **целевая** задержка для чек-листа режиссёра. В v1 платформа **не** читает фактическое значение из OBS (Frozen F7).

---

## Как включить (режиссёр)

1. Открой OBS → **Настройки** → **Дополнительно** → **Задержка трансляции (Stream Delay)**.
2. Поставь значение из панели режиссёра (или ~90–120 с, если hint не задан).
3. Virtual Camera / превью для комментаторов оставь **без** этой задержки.
4. Проверь stream key Twitch в OBS → Настройки → Трансляция.
5. Сделай пробный выход в сеть или запись и убедись, что delay включён.

Полный чек-лист: `apps/director-agent/templates/README.md` §3. Тот же текст — на `/director/{matchId}` в блоке «Задержка Twitch».

---

## Что не делает Agent (v1)

- Не выставляет Stream Delay через OBS WebSocket.
- Не гоняет FFmpeg delay-buffer (это fallback v2 по ADR-024).
- Dashboard **не** ходит в OBS напрямую (A8).

---

## API / UI

| Источник | Поле |
|----------|------|
| `tournaments.settings` | `configured_broadcast_delay_seconds` |
| `GET /api/v1/matches/{id}` | то же поле (hint для director) |
| Director UI | блок «Задержка Twitch» + чек-лист |

---

## Вне scope v1

- Автонастройка delay из панели  
- Verified actual OBS delay  
- FFmpeg / SRS delay pipeline  
