# Архитектурные решения (ADR)

> Формат: статус · контекст · решение · последствия.  
> Обновлять при изменении решений владельца.

---

## ADR-001 — Название продукта

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нужно нейтральное имя, не привязанное к BestTvGU |
| **Решение** | **Student Tournament Platform (STP)** |
| **Последствия** | Watermark STP на overlay; репозиторий остаётся BestCSTournaments |

---

## ADR-002 — Не MVP, вертикальные срезы

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Владелец не хочет «заглушки»; нужен рабочий продукт |
| **Решение** | Поставка **вертикальными срезами** end-to-end; первый рубеж — тестовый матч 5v5 |
| **Последствия** | Каждый эпик закрывается видимым результатом на экране/в эфире |

---

## ADR-003 — CS2-only, без мультигейм

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Обсуждался game adapter SDK для разных игр |
| **Решение** | **Только CS2.** Лёгкий internal adapter interface, **без** инвестиций в мультигейм SDK. Другие игры не в планах. |
| **Последствия** | MatchZy-специфичная логика допустима; не абстрагируем bomb/defuse «на будущее» |

---

## ADR-004 — Топология: Platform VPS + MySQL + локальный Director

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нужна переносимость; VPS только на время турнира; данные постоянны |
| **Решение** | **MySQL** — постоянный VPS на организатора. **Platform** — временный VPS. **Director Agent** — локально на ноутбуке. **CS2** — временный VPS. |
| **Последствия** | Deploy-скрипты для VPS; installer для Director Agent; platform подключается к remote MySQL |

---

## ADR-005 — MySQL + BLOB для медиа

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Всё важное должно быть в БД; не зависеть от файлов на VPS |
| **Решение** | MySQL хранит метаданные **и** медиа (логотипы, фоны) как BLOB. Soft limits: logo ≤2MB, bg ≤5MB. Migration path later (object storage). |
| **Последствия** | Размер БД растёт; бэкапы MySQL критичны; GOTV демки — durable copy после матча (ADR-034), не только CS2 disk |

---

## ADR-006 — Один ноутбук: режиссёр = оператор

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нет отдельных ПК для оператора и режиссёра |
| **Решение** | CS2 spectator + OBS + Director Agent + browser dashboard на **одном ноутбуке** |
| **Последствия** | Железо должно тянуть CS2+OBS; автокамера через GOTV auto-director |

---

## ADR-007 — Автокамера: GOTV auto-director

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нет отдельного оператора; нужна автокамера |
| **Решение** | Встроенный **GOTV auto-director** CS2 + **hotkeys** для ручного override |
| **Последствия** | Не обещаем ML/rule-based smart camera; честные ограничения CS2 |

---

## ADR-008 — Комментаторы: WebRTC в браузере с ноутбука режиссёра

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | 1–2 комментатора удалённо; low latency; видео только в браузере |
| **Решение** | **Director Agent** публикует WebRTC (live, no delay). Платформа — signaling + TURN + статусы. Комментатор открывает URL в браузере. |
| **Последствия** | Нужен coturn; NAT traversal; аудио комментаторов вне платформы (Voicemeeter → OBS) |

---

## ADR-009 — Два потока: live комментаторам, delayed Twitch

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Защита от stream sniping; комментаторы без задержки |
| **Решение** | Live WebRTC → комментаторы. Delayed (~90–120 с) → Twitch. Реализация delay: см. **ADR-024** (v1 = OBS Stream Delay). |
| **Последствия** | Virtual Camera / WebRTC без задержки; публичный stream с delay; параметр `broadcast_delay_seconds` в настройках турнира |

---

## ADR-010 — MatchZy wrap, не rewrite

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нужен tournament server environment |
| **Решение** | **MatchZy** + CounterStrikeSharp; наш **CS2 adapter** как API-обёртка |
| **Последствия** | Зависимость от MatchZy roadmap; своя логика только где плагин не покрывает |

---

## ADR-011 — Судья: мобильный веб + отложенная пауза

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Судья запрашивает проверку; пауза после раунда |
| **Решение** | State machine: review_requested → tech_pause at next round buy → forfeit or continue |
| **Последствия** | Синхронизация с game adapter; уведомления director + commentators |

---

## ADR-012 — Frontend: Svelte

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Выбор владельца |
| **Решение** | Svelte для overlay, dashboard, judge, commentator viewer |
| **Последствия** | Единый FE стек |

---

## ADR-013 — Deploy: скрипт на VPS + installer Director Agent

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Владелец делегировал выбор установщика |
| **Решение** | **Platform:** Docker Compose deploy script на VPS. **Director:** portable Windows installer. **CS2:** deploy script. Обновление: `git pull`. |
| **Последствия** | Два артефакта установки; документация runbook для организатора |

---

## ADR-014 — BestTvGU out of scope

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | BestTvGU — отдельный продукт |
| **Решение** | Интеграция **после** STP; только публичный read API |
| **Последствия** | Не блокируем разработку на BestTvGU API |

---

## ADR-015 — Watermark обязателен

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нейтральный брендинг турнира + идентификация платформы |
| **Решение** | Едва заметный watermark STP в углу overlay; не отключается |
| **Последствия** | CSS hardcoded или server-enforced |

---

## ADR-016 — Запись: GOTV only

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нужна запись матча |
| **Решение** | **GOTV/demo обязательно**; запись OBS production не обязательна |
| **Последствия** | Автодемо на CS2 VPS; хранение и привязка к match record |

---

## ADR-017 — Ручной provision VPS (фаза 1)

| | |
|---|---|
| **Статус** | accepted (temporary) |
| **Контекст** | Автоматизация provisioning не приоритет |
| **Решение** | Platform и CS2 VPS поднимаются **вручную** скриптами; автоматизация позже |
| **Последствия** | Runbook для техника; roadmap включает auto-provision |

---

## ADR-018 — Стримы игроков для судьи — вне платформы

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | На дистанционных турнирах судья смотрит демки в Discord |
| **Решение** | **Не** входит в STP; организатор организует Discord/стримы сам |
| **Последствия** | Нет scope на player stream verification в v1 |

---

## ADR-019 — Backend: Python + FastAPI

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Нужен async REST + WebSocket, быстрая разработка агентами |
| **Решение** | **Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic** |
| **Последствия** | `apps/api/`; uvicorn; `aiorcon` для RCON; `httpx` для webhooks |

---

## ADR-020 — Frontend: Svelte 5 + SvelteKit

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Предпочтение владельца; overlay в OBS требует лёгкий bundle |
| **Решение** | **Svelte 5 + Vite** (overlay); **SvelteKit** (dashboard, judge); **Tailwind CSS** |
| **Последствия** | pnpm workspace; static build за nginx |

---

## ADR-021 — Director Agent: Go + Pion WebRTC

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Ноутбук режиссёра уже нагружен CS2+OBS; нужен portable binary |
| **Решение** | **Go 1.22** — obs-websocket v5 client, **Pion WebRTC** publisher, FFmpeg capture |
| **Последствия** | `apps/director-agent/`; Windows portable exe + optional service |

---

## ADR-022 — Комментаторы: WebRTC P2P + coturn

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | 1–2 комментатора, browser only, low latency, удалённо |
| **Решение** | WebRTC из Director Agent; signaling через Platform WS; **coturn** на Platform VPS |
| **Последствия** | Без mediasoup/SFU; TURN обязателен для NAT |

---

## ADR-023 — CS2: MatchZy + STP.Bridge (CounterStrikeSharp)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Не переписывать tournament server; нужен judge pause и webhooks |
| **Решение** | **Metamod + CounterStrikeSharp + MatchZy** + свой плагин **STP.Bridge**; native Linux install |
| **Последствия** | Webhooks → Platform API; RCON fallback; CS2 не в Docker |

---

## ADR-024 — Delayed Twitch: OBS Stream Delay (v1), FFmpeg fallback

| | |
|---|---|
| **Статус** | accepted · superseded prior draft («FFmpeg first») |
| **Контекст** | Нужны ~90–120 с на публичный Twitch и **live** для комментаторов. OBS имеет **Stream Delay** на выход RTMP. Virtual Camera / WebRTC остаются без задержки. |
| **Решение** | **v1:** задержка Twitch через **OBS → Дополнительно → Задержка трансляции (Stream Delay)**. Director Agent в v1 — OBS WebSocket + WebRTC, **без** FFmpeg delay-ветки. **v2 (fallback):** FFmpeg buffer в Agent или SRS, если понадобится менять delay из панели / точнее контролировать буфер. |
| **Последствия** | Меньше процессов на ноутбуке; `configured_broadcast_delay_seconds` в настройках турнира — desired/чек-лист для OBS, не verified actual в v1; live WebRTC без delay |

---

## ADR-025 — Sources of truth (не одна MySQL)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Фраза «MySQL = source of truth» слишком широка |
| **Решение** | MySQL = **durable SoT for platform-owned state**. Round/score actual — CS2; OBS scene actual — OBS; overlay effective — platform-derived |
| **Последствия** | Запрет писать score в DB минуя game events/snapshot; см. [INVARIANTS.md](INVARIANTS.md) |

---

## ADR-026 — State dimensions: Match / Review / Production

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | `tech_pause` смешивался с MatchStatus |
| **Решение** | Отдельные измерения: **MatchStatus**, **ReviewStatus**, **agent/obs/broadcast + desired/actual production**. Турнир: draft→published→live→completed→archived |
| **Последствия** | Матч может быть `live` при `ReviewStatus=paused` |

---

## ADR-027 — Desired vs actual + reconciliation

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | RCON/OBS HTTP 200 ≠ runtime state; restarts / partitions |
| **Решение** | Platform хранит **desired**; runtimes сообщают **actual**; Agent/CS2 adapter — **reconcilers**. Events = fast path; **snapshots** = recovery; reconciliation = correctness |
| **Последствия** | Production desired authoritative; command history не replay на reconnect |

---

## ADR-028 — MySQL outbox (без message broker)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | In-process bus теряет side effects при crash после commit |
| **Решение** | Таблица `event_outbox` в той же транзакции, что aggregate; after-commit dispatcher; startup replay. Нет Kafka/Rabbit/Celery/Redis в v1 |
| **Последствия** | Domain events durable; WS всё ещё ephemeral |

---

## ADR-029 — Game commands: idempotent + ack

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | RCON не transactional; split-brain pause |
| **Решение** | Whitelist commands с `command_id`; Bridge ack; desired/actual pause; sequence на events; **GetSnapshot** для reconciliation |
| **Последствия** | Нет raw RCON из application; HTTP 200 ≠ applied |

---

## ADR-030 — Overlay WS: full snapshot (v1)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Patch protocol хрупкий при reconnect / missed messages |
| **Решение** | `overlay.snapshot` full state; `version` per match, DB-backed; patch — только если понадобится позже |
| **Последствия** | Client не хранит patch history |

---

## ADR-031 — Single API replica (v1)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | In-memory WS hub |
| **Решение** | **Architectural constraint:** Platform API = 1 replica. Redis только когда replicas > 1 |
| **Последствия** | Нельзя scale API horizontally без Redis fanout |

---

## ADR-032 — Correlation ID + aggregate version

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Live debugging; concurrent judge/director/webhook |
| **Решение** | `correlation_id` end-to-end; `matches.version` optimistic concurrency; rich audit fields |
| **Последствия** | Conflict на stale UI; traceable pipelines |

---

## ADR-033 — Protocol versions (Agent + Bridge)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Agent/Bridge деплоятся отдельно от Platform |
| **Решение** | `protocol_version` + component version в heartbeat/handshake; dashboard показывает compatible |
| **Последствия** | Soft fail / warning при mismatch |

---

## ADR-034 — Demo lifecycle before CS2 teardown

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Demo на ephemeral CS2 VPS противоречит durable recording |
| **Решение** | После матча: finalize → copy to durable storage → `demo_files` URL/path → затем teardown CS2 |
| **Последствия** | Gate «demo exists» = durable location, не только CS2 disk |

---

## ADR-035 — Health model (reachability ≠ healthy)

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | «last webhook < 30s» слишком слабо |
| **Решение** | Per-component: reachability, event freshness, command path, state consistency → HEALTHY/DEGRADED/OFFLINE/UNKNOWN. `/health` без DB; `/ready` с DB |
| **Последствия** | Dashboard показывает детальный CS2/Agent/OBS health |

---

## ADR-036 — D8 Real-time = capability, не bounded context

| | |
|---|---|
| **Статус** | accepted |
| **Контекст** | Real-time — transport, не бизнес-домен |
| **Решение** | Business domains: D1–D7. Platform capabilities: Realtime, Operations, Security, Persistence. D7 Overlay остаётся domain (merge invariants) |
| **Последствия** | LAYERS.md: D8 не BC; frontend — feature-oriented, не 4 папки на каждый CRUD |
