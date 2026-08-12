# TZ009 — Owner smoke (≤ 30 мин)

> Live CS2 Local GATE. **DS → Bridge → Platform → счёт** (без Fake-эмулятора).  
> Установка: [LOCAL-CS2-DS.md](../../../infra/game-server/LOCAL-CS2-DS.md) § Live-матч  
> API: [game-server README](../../../infra/game-server/README.md) § Live локальный DS  
> Трек: [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md) §1  
> ТЗ: [tasks/009_LIVE-CS2-LOCAL.md](../../../tasks/009_LIVE-CS2-LOCAL.md)

| Поле | Значение |
|------|----------|
| **CI Fake** | ✅ `verify.ps1` → VERIFY OK — TZ009 (P5; CS2 DS не нужен) |
| **Primary GATE (live DS)** | ⏳ **gate_ready** — ждёт проход @owner ниже |
| **`live_cs2_local=done`** | только после отметки @owner (Frozen F5) |

---

## Подготовка (один раз)

Плагины + `gameinfo.gi` — как в LOCAL-CS2-DS. Секреты — в корневом `.env`.

## Быстрый путь (рекомендуется)

```powershell
cd C:\BestCSTournaments
.\scripts\live-cs2-local.ps1
```

Дальше: `connect 127.0.0.1:27015` → раунд → проверь `GET /api/v1/matches/m_live_cs2`.  
Если Bridge писал старые MatchId — **рестарт** окна dedicated после скрипта.

---

## Подготовка (ручная, если без скрипта)

---

## Чеклист smoke

Отмечай по мере прохождения:

- [ ] **1.** `start-dedicated-competitive.bat` — в логе MatchZy + `STK.Bridge loading… version=0.2.0`
- [ ] **2.** `GET http://127.0.0.1:27099/health` → `role=stk-bridge`, `protocol_version=1`
- [ ] **3.** Создан матч (админка или API) — есть `match_id`
- [ ] **4.** `POST /api/v1/game-servers` — `endpoint_url=http://127.0.0.1:27099`, тот же secret
- [ ] **5.** `POST …/matches/{id}/assign-server` — у матча `game_server_id` ≠ `srv_fake`
- [ ] **6.** Bridge `config.json`: `MatchId` / `ServerId` / `WebhookSecret` / `PlatformUrl` → рестарт DS
- [ ] **7.** **Старт на локальном сервере** (или `POST …/start-live`) — статус `live`
- [ ] **8.** `connect 127.0.0.1:27015` — сыгран ≥1 раунд; в логе Bridge `emit round_start` / `round_end`
- [ ] **9.** `GET /api/v1/matches/{id}` — видны счёт и/или раунд
- [ ] **10.** (Опц.) Судья: pause → команда на `:27099`

**Не в этом smoke:** Twitch, VPS CS2, кнопка «Старт (Fake)».

### Быстрые команды (если без UI)

```powershell
# после логина организатора — токен в $tok
$base = "http://127.0.0.1:8000"
$secret = $env:CS2_WEBHOOK_SECRET   # или значение из .env
$hdr = @{ Authorization = "Bearer $tok"; "Content-Type" = "application/json" }

Invoke-RestMethod -Method POST "$base/api/v1/game-servers" -Headers $hdr -Body (@{
  server_id = "srv_local"; endpoint_url = "http://127.0.0.1:27099"
  webhook_secret = $secret; host = "127.0.0.1"; port = 27015
} | ConvertTo-Json)

Invoke-RestMethod -Method POST "$base/api/v1/matches/<MATCH_ID>/assign-server" -Headers $hdr `
  -Body '{"server_id":"srv_local"}'

Invoke-RestMethod -Method POST "$base/api/v1/matches/<MATCH_ID>/start-live" -Headers $hdr
Invoke-RestMethod "$base/api/v1/matches/<MATCH_ID>"
```

---

## После успешного прохода (@owner)

1. Здесь: **Статус Primary GATE** → ✅ passed; таблица ниже.
2. [ALPHA-LIVE-TRACKS.md](../../../docs/ALPHA-LIVE-TRACKS.md): `live_cs2_local` → **done** + дата.
3. [tasks/009](../../../tasks/009_LIVE-CS2-LOCAL.md) §5 чеклист; статус ТЗ → **done**.
4. [ROADMAP.md](../../../docs/ROADMAP.md) — строка live CS2.
5. По желанию [post-mortem](../../../docs/alpha/POST-MORTEM-TEMPLATE.md).

| Поле | Значение |
|------|----------|
| Пройдено @owner | |
| Дата | |
| Заметка | |

---

## Если сломалось

| Симптом | Что проверить |
|---------|----------------|
| `:27099` молчит | DS не запущен / `CommandListenHost` ≠ `127.0.0.1` / порт занят |
| `start-live` 400 | Сначала assign (не Fake start) |
| Нет heartbeat / round в API | Secret / MatchId / ServerId в Bridge ≠ Platform |
| Metamod пустой | Останови DS → `patch-gameinfo-metamod.bat` |
| Старый плагин | `dotnet build -c Release` → copy DLL (сохрани config) |
