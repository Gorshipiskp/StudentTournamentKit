# apps/judge — Панель судьи

Мобильный веб-UI по **invite-ссылке**: запросить проверку → дождаться паузы → **продолжить** или **тех. поражение**.

**UI:** токены BestMomentsMaker ([`packages/ui-tokens`](../../packages/ui-tokens)) — dark stage · amber · Sora.

**Статус:** working (TZ004 + UX redesign).

## Dev

```bash
# API на :8000
cd apps/judge
npm install
npm run dev
```

На телефоне / DevTools mobile:

```text
http://127.0.0.1:5175/?token=<invite_raw>
```

Создать invite (из админки «Получить ссылки» или curl):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/invites \
  -H "Content-Type: application/json" \
  -d '{"match_id":"m_xxx","role":"judge"}'
```

В ответе `token` — один раз в URL судье. Без `?token=` — «Доступ закрыт».

## Поведение на экране

| Состояние | Что видит судья |
|-----------|-----------------|
| нет / отменена / завершена | **Запросить проверку** |
| запрошена | Подсказка про закупку + **Отменить проверку** |
| пауза готовится | Индикатор ожидания |
| тех. пауза | **Продолжить матч** / **Техническое поражение…** (выбор команды + подтверждение) |

Статус обновляется по WebSocket (`/ws/judge`) и запасным опросом HTTP. Действия — Bearer после `POST /api/v1/invites/redeem`.

## Build

```bash
npm run build   # → dist/
npm test
```

Прод (nginx): `dist/` → `html/judge/`, location `/judge/` (см. `infra/platform/nginx/default.conf`).
