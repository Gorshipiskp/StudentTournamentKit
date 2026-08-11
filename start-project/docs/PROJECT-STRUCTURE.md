# Структура репозитория с ИИ-командой

> Создай при bootstrap. Пути в `{{…}}` — заменить.  
> **Не всё обязательно:** уровни S/M/L — [../SETUP.md](../SETUP.md).

```text
{{REPO_SLUG}}/
├── AGENTS.md                 # онбординг всех ролей (из start-project/AGENTS.md)
├── PROJECT.md                # hub: старт, ссылки, команда
├── README.md                 # быстрый старт для людей
│
├── workers/                  # память ИИ-команды
│   ├── README.md
│   ├── ROLES.md
│   ├── TOKEN-HYGIENE.md
│   ├── IDEAS.md
│   ├── CODE_CHANGE_BOARD.md
│   ├── sprint/
│   │   ├── CURRENT.md
│   │   ├── ORCHESTRATOR.md
│   │   └── archive/
│   ├── team-lead/
│   ├── developer/
│   ├── … (14 ролей)
│   └── _templates/
│
├── overview/                 # продукт (documentarian)
│   ├── README.md
│   ├── product.md
│   ├── architecture.md
│   ├── code-map.md
│   └── commercial.md         # опционально
│
├── {{TECH_OVERVIEW_PATH}}/   # техника (scout)
│   ├── README.md             # матрица doc_coverage / test_coverage
│   ├── 00-glossary.md
│   ├── 01-monorepo-map.md
│   ├── systems/
│   └── components/
│
├── {{TASKS_PATH}}/           # ТЗ на фичи (team-lead + documentarian)
│   ├── README.md
│   └── NNN_FEATURE.md
│
├── {{MAIN_APP_PATH}}/        # основное приложение
├── {{BACKEND_PATH}}/         # API
│
├── .cursor/
│   ├── skills/
│   │   ├── _shared/WORKER-STANDARDS.md
│   │   ├── agent-start/SKILL.md
│   │   ├── prompt-runbook/SKILL.md
│   │   └── <role>/SKILL.md   # по мере роста
│   └── rules/
│       ├── clear-writing.mdc
│       └── token-hygiene.mdc
│
└── scripts/
    └── verify.ps1            # или verify.sh — единая проверка
```

## Минимум для «команда работает»

| Путь | S | M | L |
|------|---|---|---|
| `workers/developer/` (+ WORKLOG) | да | да | да |
| `AGENTS.md` (сокращённый) | да | да | да |
| `PROJECT.md` | да | да | да |
| `workers/team-lead/` | опц. | да | да |
| `overview/product.md` | опц. | да | да |
| `tasks/` | нет | да | да |
| `workers/sprint/CURRENT.md` | нет | опц. | да |
| `tech-overview/` + scout | нет | опц. | да |
| все 14 ролей | нет | нет | по необходимости |

## Секреты

`config/secrets/` или `.env` — **вне** `workers/`, в `.gitignore`.
