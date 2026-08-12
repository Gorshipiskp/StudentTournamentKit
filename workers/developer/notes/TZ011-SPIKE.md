# TZ011-SPIKE — MediaMTX + WHIP/WHEP

**Дата:** 2026-08-12  
**Образ:** `bluenviron/mediamtx:1.12.2`  
**Конфиг:** `infra/mediamtx/mediamtx.yml` · compose profile `whip`

## Вердикт

| Проверка | Результат |
|----------|-----------|
| Compose MediaMTX up | **OK** |
| Path `stk/<matchId>` | **OK** (`stk/m_spike`) |
| WHEP в браузере → видео | **OK** (testsrc 640×360, `ice: connected`) |
| OBS WHIP publish | **Pending @owner** (на этой машине OBS не гоняли; URL готовы) |
| OBS WHIP ∥ Twitch одновременно | **Ожидаемо НЕТ в одном Service** — см. ниже; подтвердить на версии @owner |

## URL (local defaults)

| Роль | URL |
|------|-----|
| WHIP (OBS Service=WHIP) | `http://127.0.0.1:8889/stk/<matchId>/whip` |
| WHEP | `http://127.0.0.1:8889/stk/<matchId>/whep` |
| Built-in read UI | `http://127.0.0.1:8889/stk/<matchId>` |
| Spike page | `infra/mediamtx/spike/whep.html` (serve locally) |
| Control API | `http://127.0.0.1:9997/v3/paths/list` |
| Env public base | `MEDIAMTX_PUBLIC_URL=http://127.0.0.1:8889` |

Пример матча spike: `matchId=m_spike` →  
`…/stk/m_spike/whip` · `…/stk/m_spike/whep`.

## Как воспроизвести (без OBS — lab)

```powershell
# 1) MediaMTX
docker compose --env-file .env -f infra/platform/docker-compose.yml --profile whip up -d mediamtx

# 2) Publisher = test pattern via RTSP/TCP (замена OBS для lab)
ffmpeg -hide_banner -re `
  -f lavfi -i testsrc=size=640x360:rate=30 `
  -f lavfi -i sine=frequency=440:sample_rate=48000 `
  -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -g 30 `
  -c:a aac -f rtsp -rtsp_transport tcp `
  rtsp://127.0.0.1:8554/stk/m_spike

# 3) Проверка publisher
curl.exe http://127.0.0.1:9997/v3/paths/get/stk/m_spike
# expect: ready=true, tracks H264

# 4) WHEP page
cd infra/mediamtx/spike
python -m http.server 8765 --bind 127.0.0.1
# браузер: http://127.0.0.1:8765/whep.html → Play
```

**Доказательство lab (2026-08-12):**  
лог страницы: `track: video` / `track: audio` / `ice: connected` / `WHEP OK`;  
`videoWidth=640`, `videoHeight=360`; MediaMTX: `is reading from path 'stk/m_spike', 1 track (H264)`.

## OBS WHIP (для @owner)

1. Settings → Stream → Service **WHIP**  
2. Server: `http://<MEDIAMTX_HOST>:8889/stk/<matchId>/whip`  
3. Bearer: пусто на spike; на prod — токен из Platform (P3)  
4. Start Streaming  
5. Открыть WHEP page / built-in UI на том же path  

Документация MediaMTX: Service `WHIP`, URL `…/mystream/whip`.

## ICE / NAT notes

- Порты: **8889/tcp** (WHIP/WHEP HTTP), **8189/udp** (ICE).  
- В Docker lab ICE сошёлся на host-candidate контейнера (`172.20.0.x:8189`) ↔ браузер на хосте.  
- На **VPS** обязательно: `MEDIAMTX_WEBRTC_ADDITIONAL_HOSTS=<public-ip-or-dns>` (пробрасывается в `MTX_WEBRTCADDITIONALHOSTS`).  
- Если UDP режется фаерволом: раскомментировать `webrtcLocalTCPAddress: :8189` и открыть TCP 8189.  
- Домашний OBS → VPS: при необходимости coturn (`webrtcICEServers2` + `TURN_*`, profile `webrtc`) — донастройка в P2/P3.  
- HTTPS/TLS для prod WHIP handshake — позже (nginx); localhost HTTP ok.

## OBS: WHIP + Twitch одновременно

**Черновой вердикт (до подтверждения версии @owner):**

| Вопрос | Ответ |
|--------|--------|
| Один Settings → Stream = WHIP **и** Twitch? | **Нет.** В stock OBS один primary Stream service. |
| Обход | (A) Stream = **WHIP**, Twitch через **второй выход** (plugin multi-RTMP / вторая инстанция OBS / Custom FFmpeg output на RTMP). (B) На матч без публичного Twitch — только WHIP. |
| WHIP «simulcast layers» | Не путать с dual-destination; это слои качества в одном WHIP (и то ещё не везде в UI). |

**Канон STK после spike:** Twitch (с Stream Delay) и WHIP (live комментаторам) — **два выхода**; delay только на Twitch (Frozen F6).

**@owner:** вписать версию OBS + факт «получилось / не получилось» dual-output на своей машине (P6 smoke / раньше).

## ADR

Черновик: [ADR-037-DRAFT.md](ADR-037-DRAFT.md) — MediaMTX на Platform supersede ADR-022 **для live**. Merge в DECISIONS — **P2**.

## Вне scope этого spike

- Platform credentials API (P3)  
- `/watch` WHEP UI (P4)  
- Удаление Pion/Fake  
