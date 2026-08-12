# Памятка режиссёра — день Alpha

> Кому: человек у ноутбука эфира (панель + Agent; на Fake — без живого OBS).  
> Общий день: [ALPHA-RUNBOOK.md](../ALPHA-RUNBOOK.md) · production hub: [PRODUCTION-RUNBOOK.md](../PRODUCTION-RUNBOOK.md) · OBS-сцены: [templates/README.md](../../apps/director-agent/templates/README.md).

---

## Что открыть

1. Ссылку режиссёра от организатора → `/director/{матч}` (обычно порт `5174`).
2. **Agent** на той же машине (или рядом), привязанный к этому матчу.

### Alpha на Fake (основной путь)

```text
cd apps/director-agent
# .env: STK_MATCH_ID, STK_AGENT_TOKEN (как в корневом .env)
go run ./cmd/agent --fake-obs
# или: .\stk-director-agent.exe --fake-obs --match <MATCH_ID>
```

Живой OBS не обязателен для приёмки Fake. Когда понадобится реальный OBS — имена шести сцен и WebSocket: [templates/README.md](../../apps/director-agent/templates/README.md) §1–2.

---

## На панели режиссёра

| Блок | Зачем |
|------|--------|
| Сцены | Крупные кнопки + клавиши **1–6**. Главное действие пульта |
| Предупреждения | Только если агент/OBS не на связи или судья объявил паузу |
| Проблемы | Список только «сломанных» частей эфира |
| Дополнительно | Табло, чек-лист задержки Twitch, короткий журнал — свёрнуто по умолчанию |

Контракты: [BROADCAST-HEALTH.md](../BROADCAST-HEALTH.md) · [BROADCAST-DELAY.md](../BROADCAST-DELAY.md).

---

## Чек-лист перед «эфиром»

- [ ] Панель открылась по ссылке организатора
- [ ] Agent запущен с `--fake-obs` (или с паролем OBS)
- [ ] В «Состоянии эфира» агент не «Нет связи»
- [ ] Смена сцены доходит до overlay (`/overlay/{матч}`)
- [ ] Картинка overlay: студенческий «campus» вид (бирюза/янтарь или брендинг), watermark на месте
- [ ] На сцене «Игра» табло сверху не мешает центру кадра; счёт обновляется заметно
- [ ] Чек-лист задержки просмотрен (на live Twitch — Stream Delay ~90–120 с в OBS → Дополнительно)

На live Twitch Agent **не** включает задержку сам — только ты в OBS ([templates §3](../../apps/director-agent/templates/README.md)).

---

## Реальное видео комментаторам (канон — WHIP)

Для Alpha Fake GATE это **не обязательно**. На матч-день:

1. Подними MediaMTX: `docker compose --profile whip up -d mediamtx` ([infra/mediamtx](../../infra/mediamtx/README.md)).
2. Agent — **только сцены** (реальный OBS). **Не** нужен `--live-webrtc` / Virtual Camera / FFmpeg.
3. Возьми WHIP URL + bearer: `POST /api/v1/matches/{id}/whip-publish` (логин организатора).
4. OBS → Settings → Stream → Service **WHIP** → Server = `whip_url`, Bearer = token → **Start Streaming**.  
   Twitch — **отдельный** выход (Stream Delay только на Twitch).
5. Ссылка комментатора `/watch?token=…` (по умолчанию WHEP). Репетиция Fake: `?media=fake` + Agent `--fake-webrtc`.

Подробности: [Agent README §4d](../../apps/director-agent/README.md) · [WEBRTC-CONTRACT](../WEBRTC-CONTRACT.md) · трек [ALPHA-LIVE-TRACKS](../ALPHA-LIVE-TRACKS.md) (`live_whip`) · smoke [TZ011-OWNER-SMOKE](../../workers/developer/notes/TZ011-OWNER-SMOKE.md).

| Симптом | Что сделать |
|---------|-------------|
| «Режиссёр ещё не начал эфир (WHIP)» | Start Streaming в OBS; проверь MediaMTX / path `stk/<matchId>` |
| 401/403 на WHIP | Обнови bearer из `whip-publish` |
| Нужен старый VC-путь | Legacy `--live-webrtc` (deprecated) — только отладка |

---

## Если что-то не так

Полная таблица: [PRODUCTION-RECOVERY.md](../PRODUCTION-RECOVERY.md).

| Симптом | Что сделать |
|---------|-------------|
| Агент / OBS «Нет связи» | Перезапусти Agent; проверь `STK_AGENT_TOKEN` и id матча |
| Сцена в панели есть, в OBS нет | Имена сцен в OBS должны совпадать один в один (регистр) |
| Overlay пустой / старый | Обнови Browser Source; открой `/overlay/{матч}` напрямую |
| Не уверен в стенде | [organizer.md](organizer.md) · `.\scripts\alpha-dry-run.ps1` |

Судье отдельная ссылка — [judge.md](judge.md). Тебе достаточно видеть статус разбора в журнале / на панели.
