# OBS template — StudentTournamentKit

Заготовка сцен для ноутбука режиссёра. Имена сцен **должны совпадать** с Platform
`desired.scene`: `waiting` · `intro` · `teams` · `ingame` · `break` · `winner`.

Машиночитаемый список: [`scenes.json`](scenes.json).

> Полноценный экспорт OBS Scene Collection (бинарный/тяжёлый JSON OBS) в v1 не
> коммитим — ниже ручная сборка за 5–10 минут. Agent переключает сцены по **имени**.

---

## 1. Создать сцены в OBS

1. Открой OBS Studio 30+.
2. Создай шесть сцен с **точными** именами из списка выше (регистр важен).
3. На каждой сцене добавь **Источник браузера** «STK Overlay»:

| Поле | Значение |
|------|----------|
| URL | `http://127.0.0.1:8080/overlay/<MATCH_ID>` (nginx) **или** `http://127.0.0.1:5173/overlay/<MATCH_ID>` (vite dev) |
| Ширина × высота | 1920 × 1080 |
| FPS | 30 |
| Завершать работу, когда не видно | **выкл.** (иначе WS рвётся) |
| Обновлять браузер при активации сцены | по желанию вкл. |

4. На сцене `ingame` добавь захват CS2 (Game/Window Capture) **под** overlay.
5. Замени `<MATCH_ID>` на id матча из Platform (`POST /api/v1/matches` → `id`).

Опционально: экспортируй Scene Collection из OBS («Профиль / Коллекция сцен → Экспорт»)
и храни локально — в git секреты/абсолютные пути не класть.

---

## 2. WebSocket OBS (для Agent)

OBS → **Инструменты → Настройки WebSocket-сервера**:

- Включить сервер
- Порт: `4455` (по умолчанию)
- Пароль: свой (только в `.env` агента / флаге `--obs-password`)

Agent — **единственный**, кто ходит в OBS (инвариант A8). Панель режиссёра OBS не трогает.

---

## 3. Stream Delay (Twitch) — чек-лист v1

Задержка публичного эфира = **OBS Stream Delay**, не FFmpeg в Agent (ADR-024 v1).  
Контракт для режиссёра/продукта: [`docs/BROADCAST-DELAY.md`](../../../docs/BROADCAST-DELAY.md).

- [ ] Настройки → **Дополнительно** → **Задержка трансляции (Stream Delay)**
- [ ] Значение ~ **90–120 с** (как в настройках турнира / продукте)
- [ ] Комментаторы **без** этой задержки: OBS **WHIP** → MediaMTX → `/watch` (канон TZ011)  
      ([Agent README §4d](../README.md) · [director.md](../../../docs/alpha/director.md) · [WEBRTC-CONTRACT](../../../docs/WEBRTC-CONTRACT.md))
- [ ] Legacy Virtual Cam + `--live-webrtc` — **не** использовать на матч-день
- [ ] Проверить, что Twitch stream key введён в OBS → Настройки → Трансляция (отдельный выход от WHIP)
- [ ] Пробный выход в сеть / запись — убедиться, что delay включён

Agent **не** выставляет delay автоматически в v1.  
**Не путать:** Stream Delay = только Twitch; WHIP → `/watch` идёт **без** этой задержки.

---

## 4. Проверка с Agent

```powershell
cd apps/director-agent
copy .env.example .env
# заполни STK_MATCH_ID, STK_AGENT_TOKEN, STK_OBS_PASSWORD

go build -o stk-director-agent.exe ./cmd/agent
.\stk-director-agent.exe
# или без OBS:
.\stk-director-agent.exe --fake-obs --match <MATCH_ID>
```

Из панели `/director/<MATCH_ID>` или curl смени сцену → в OBS должна переключиться
одноимённая сцена; в API `actual.scene` совпадает с desired.
