# apps/judge — Панель судьи

Мобильный веб-UI по **invite-ссылке**: запрос проверки → пауза → продолжить / тех. поражение.

**Статус:** working (TZ004 P2).

## Dev

```bash
# API на :8000
cd apps/judge
npm install
npm run dev
```

Откройте на телефоне / DevTools mobile:

```text
http://127.0.0.1:5175/?token=<invite_raw>
```

Создать invite (organizer / curl):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/invites \
  -H "Content-Type: application/json" \
  -d '{"match_id":"m_xxx","role":"judge"}'
```

В ответе поле `token` — один раз показать судье в URL.

Без `?token=` — экран «Доступ закрыт».

## Поведение

| Состояние проверки | Кнопки |
|--------------------|--------|
| нет / отменена / завершена | **Запрос проверки** |
| запрошена | **Отменить** (+ ожидание паузы на round buy) |
| пауза готовится | только статус |
| тех. пауза | **Продолжить** / **Тех. поражение** (выбор команды) |

Статус матча опрашивается каждые ~2 с (`GET /api/v1/matches/{id}`). Действия — Bearer после `POST /api/v1/invites/redeem`.

## Build

```bash
npm run build   # → dist/
npm test
```

Прод (nginx): скопировать `dist/` → `html/judge/`, location `/judge/` (см. `infra/platform/nginx/default.conf`).
