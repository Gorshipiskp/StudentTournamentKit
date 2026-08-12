# Overlay UI — owner smoke (campus broadcast)

> После редизайна P1–P4 · контракт snapshot не менялся · OBS canvas прозрачный.

## Быстрый проход (~10 мин)

### OBS overlay

1. `cd apps/overlay && npm run dev` → открой `http://127.0.0.1:5173/overlay/<matchId>`
2. В пульте режиссёра пройди сцены: Ожидание → Интро → Команды → Игра → Перерыв → Победитель
3. На каждой сцене: читаемые имена, bone/amber (или цвета брендинга), watermark внизу справа
4. Игра: denser табло сверху, LIVE, счёт «подпрыгивает» при изменении
5. Фон страницы прозрачный (серая клетка / пустота браузера — ок; в OBS поверх игры)
6. Debug-метка сцены только с `?debug=1`

### Branding (если есть лого/цвета турнира)

7. На waiting/intro/teams/break/winner видно **BrandMark** (лого + имя)
8. На ingame лого — бейдж в углу; цвета A/B из branding

### Комментатор `/watch`

9. Invite → boot «Комментатор» → табло + сцена
10. Клавиши **M** / **F**; ожидание эфира без жаргона WHIP
11. Счёт мигает при обновлении overlay WS

## Не регрессии

- [ ] Watermark нельзя выключить
- [ ] Judge banner виден
- [ ] `npm run build` + `npm test` в `apps/overlay`
