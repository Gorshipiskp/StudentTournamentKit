# TZ011 — Owner smoke (≤ 30 мин)

> OBS **WHIP** → MediaMTX → `/watch` **WHEP**. Без Virtual Camera / FFmpeg.  
> ТЗ: [tasks/011_OBS-WHIP.md](../../../tasks/011_OBS-WHIP.md)  
> Трек: [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md) §5 `live_whip`  
> Spike: [TZ011-SPIKE.md](TZ011-SPIKE.md) · контракт: [WEBRTC-CONTRACT.md](../../../docs/WEBRTC-CONTRACT.md)

| Поле | Значение |
|------|----------|
| **CI Fake** | ✅ `verify.ps1` → VERIFY OK — TZ011 (MediaMTX **не** нужен) |
| **Primary GATE (WHIP)** | ⏳ **gate_ready** — ждёт проход @owner ниже |
| **`live_whip=done`** | только после отметки @owner |

---

## Подготовка

В корневом `.env` (без секретов в чат/WORKLOG):

- `MEDIAMTX_PUBLIC_URL`, `MEDIAMTX_API_URL`, `MEDIAMTX_AUTH_SECRET`
- `MEDIAMTX_WEBRTC_ADDITIONAL_HOSTS` (LAN IP или публичный IP VPS)

```powershell
cd C:\BestCSTournaments
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx
.\scripts\dev-remote.ps1 -MatchId m_whip
# или live-cs2-local.ps1 — Agent только сцены (без --live-webrtc)
```

---

## Чеклист smoke

Отмечай по мере прохождения:

### 1. MediaMTX

```powershell
curl.exe http://127.0.0.1:9997/v3/paths/list
```

- [ ] ответ JSON, контейнер Up

### 2. WHIP credentials (organizer)

```powershell
# login → access_token, затем:
curl.exe -sS -X POST "http://127.0.0.1:8000/api/v1/matches/<MATCH_ID>/whip-publish" `
  -H "Authorization: Bearer <organizer_token>"
```

- [ ] есть `whip_url`, `bearer`, `path` = `stk/<MATCH_ID>` (**не** логировать bearer)

### 3. OBS

- [ ] Settings → Stream → Service **WHIP** → Server = `whip_url`, Bearer = token → **Start Streaming**
- [ ] Twitch (если нужен) — **отдельный** выход; Stream Delay только на Twitch
- [ ] Версия OBS: ________  WHIP∥Twitch: два выхода / plugin / 2× OBS: ________

### 4. `/watch`

- [ ] Staff commentator link → `/watch?token=…` → **видео Program OBS**
- [ ] Качество/задержка субъективно лучше TZ008 VC (нет двойного encode)
- [ ] Stop Streaming в OBS → текст «Режиссёр ещё не начал эфир (WHIP)»
- [ ] (опц.) `GET /api/v1/matches/<id>/health` → `components.whip` publisher online

### 5. Fake regression

- [ ] Agent `--fake-webrtc` + `/watch?media=fake` — картинка-заглушка OK

---

## После прохода (@owner)

1. ALPHA-LIVE §5 / сводка: `live_whip=done` + дата + заметка  
2. `tasks/011_OBS-WHIP.md` → **done**; §5 Primary галочки  
3. Коммиты только @owner  

Далее TL: **live Twitch** или **TZ010 Production Ready**.
