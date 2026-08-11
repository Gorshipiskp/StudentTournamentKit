# Bootstrap prompt для агента (копипаст в пустой проект)

```text
В репозитории лежит папка start-project/ — переносимый набор ИИ-команды.

Задача: развернуть команду под ЭТОТ проект по start-project/SETUP.md.

Профиль (заполни из кода и спроси владельца что неясно):
- project_name: …
- repo_slug: …
- main_app_path: …
- backend_path: …
- team_scale: S | M | L  ← согласовать с владельцем; не разворачивать лишние роли

Шаги:
1. Прочитай start-project/README.md (§ «набор тяжёлый»), PHILOSOPHY.md, workers/ROLES.md, SETUP § «Масштаб команды».
2. Создай структуру папок **по уровню S/M/L**, не обязательно полный монорепо-каркас.
3. Скопируй и адаптируй файлы из start-project/ — замени плейсхолдеры.
4. IDENTITY — только для ролей, которые реально нужны (см. ALL-ROLES-IDENTITY.md).
5. sprint/CURRENT.md из CURRENT-TEMPLATE.md — спринт «Bootstrap команды».
6. Черновики overview/product.md, architecture.md, code-map.md — AS-IS по коду, без выдумок.
7. AGENTS.md в корень из start-project/AGENTS.md.
8. PROJECT.md — hub со ссылками.

Не делай: продуктовые фичи; коммит без @owner; секреты в workers/.

Отчёт:
- выбранный уровень S/M/L и почему;
- дерево созданных путей;
- что **намеренно не** развернули (и почему);
- что нужно от владельца;
- рекомендация по первому чату (Team Lead или solo developer).
```
