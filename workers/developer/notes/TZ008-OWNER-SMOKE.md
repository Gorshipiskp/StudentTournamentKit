# TZ008 — Owner smoke (≤ 25 мин)

> Live WebRTC GATE. **OBS Virtual Camera → Agent `--live-webrtc` → `/watch`**.  
> Контракт: [docs/WEBRTC-CONTRACT.md](../../../docs/WEBRTC-CONTRACT.md) § Live source  
> Agent: [apps/director-agent/README.md](../../../apps/director-agent/README.md) §4c  
> Памятка: [docs/alpha/director.md](../../../docs/alpha/director.md)  
> Трек: [docs/ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md)

**Статус Primary GATE:** ✅ **passed** (2026-08-12 @owner — real OBS + `/watch`).  
CI / Alpha Fake: `--fake-webrtc` (без OBS) — уже в `verify.ps1`.  
`live_twitch` / `live_cs2` — **не** этот smoke.

**Качество:** после приёмки defaults Agent = 1080p / 3500k / `deadline=good`. Перезапусти Agent с новым `stk-director-agent.exe`.

---

## Подготовка

1. OBS Studio: сцены STK + Browser Source overlay ([templates](../../../apps/director-agent/templates/README.md)).
2. OBS → **Запустить виртуальную камеру** (Start Virtual Camera).
3. Stream Delay Twitch **не** на Virtual Cam ([templates §3](../../../apps/director-agent/templates/README.md)).
4. FFmpeg на PATH или запомни путь (часто `C:\ffmpeg\bin\ffmpeg.exe`).
5. Platform + overlay:

```powershell
cd infra/platform
docker compose --env-file ../../.env.example up -d mysql

cd ../../apps/api
# MYSQL_* / STK_* из .env.example
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# другой терминал:
cd apps/overlay; npm run dev   # :5173 — /watch
```

Проверка устройства:

```powershell
ffmpeg -hide_banner -list_devices true -f dshow -i dummy
# ожидаем: "OBS Virtual Camera" (video)
```

---

## Шаги

| # | Действие | Ожидание |
|---|----------|----------|
| 1 | `GET http://127.0.0.1:8000/health` | 200 |
| 2 | `POST /api/v1/matches` `{match_id:"m_live_webrtc", …}` или матч из админки | матч есть |
| 3 | OBS Virtual Camera **включена** | устройство отдаёт кадры |
| 4 | Agent: `--fake-obs --live-webrtc --match m_live_webrtc --token … --webrtc-ffmpeg …` | лог: `live-webrtc publisher started`; **нет** `--fake-webrtc` |
| 5 | `POST /api/v1/invites` role=`commentator` для матча | `token` в ответе |
| 6 | Открыть `http://127.0.0.1:5173/watch?token=<invite>` (**без** `mock=1`) | **Реальная** картинка OBS (не цветная test-заглушка) |
| 7 | Сменить сцену в OBS / панели | На `/watch` видно изменение (с задержкой encode) |
| 8 | Ctrl+C Agent → снова `--live-webrtc` | `/watch` переподключается, video снова есть |
| 9 | `.\scripts\verify.ps1` | **VERIFY OK — TZ008** (Fake CI; OBS не нужен) |

### Быстрые команды

```powershell
# Agent live
cd apps/director-agent
.\stk-director-agent.exe --fake-obs --live-webrtc `
  --platform http://127.0.0.1:8000 --match m_live_webrtc `
  --token dev_agent_token_change_me `
  --webrtc-ffmpeg C:\ffmpeg\bin\ffmpeg.exe

# Invite (после login organizer / или как в TZ004)
# POST /api/v1/invites  {"role":"commentator","match_id":"m_live_webrtc", …}
```

---

## Чеклист приёмки @owner

- [ ] Virtual Camera включена; устройство `OBS Virtual Camera` в `ffmpeg -list_devices`
- [ ] Agent `--live-webrtc` без ошибок ffmpeg в логе
- [ ] `/watch` показывает **эфир OBS**, не Fake-паттерн
- [ ] Рестарт Agent → video возвращается
- [ ] `verify.ps1` зелёный
- [ ] Подпись: дата ______ · **принято / не принято** · комментарий: ______

---

## Блокеры / notes

| Тема | Статус |
|------|--------|
| Fake WebRTC (`--fake-webrtc`) | CI / не этот smoke |
| Live Virtual Cam → `/watch` | **этот GATE** |
| NAT / TURN за LAN | optional |
| Twitch Stream Delay | отдельный трек `live_twitch` |

**Критерий:** шаги 1–9 ≤ 25 мин без устных пояснений разработчика.
