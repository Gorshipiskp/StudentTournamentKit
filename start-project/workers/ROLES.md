# Матрица ролей ИИ-команды

> Подробные IDENTITY: `workers/roles/<slug>/IDENTITY.md` → копировать в `workers/<slug>/`.  
> **Справочник максимального состава.** В маленьком проекте заведи только строки, которые реально используешь.

| Папка | Роль | Фокус | Типичные задачи | Эскалация |
|-------|------|-------|-----------------|-----------|
| `team-lead/` | Team Lead | Приоритеты, ТЗ, координация | Декомпозиция, спринт, runbook | Владелец; все роли |
| `developer/` | Developer | Фичи end-to-end | API, UI, миграции, тесты в scope | tester, optimizer, cybersecurity, devops |
| `tester/` | QA | Приёмка, регрессия | Чеклисты ТЗ, verify, баг-репорты | developer, team-lead |
| `cybersecurity/` | Security | Угрозы, auth, секреты | Threat model, review RBAC | developer, devops |
| `optimizer/` | Optimizer | Качество без смены поведения | Рефакторинг, perf, arch checks | developer, team-lead |
| `devops/` | DevOps | CI, Docker, деплой | verify, release, env schema | developer, cybersecurity |
| `documentarian/` | Documentarian | Docs ↔ код | overview/, tasks/, PROJECT.md | team-lead, developer |
| `sales/` | Sales | КП, pitch | commercial, pricing drafts | team-lead, владелец |
| `smm/` | SMM | Посты, анонсы | TG/VK черновики | team-lead, documentarian |
| `scout/` | Scout | tech-overview | doc_coverage, CODE_CHANGE_BOARD | documentarian, tester |
| `code-reviewer/` | Code Reviewer | Ревью diff | Findings, targeted tests | developer, team-lead |
| `outcome-ux/` | Outcome UX | Поток, ясность, тихие провалы | AUDIT notes, идеи UX | team-lead, designer, developer |
| `designer/` | Designer | Дизайн-система, визуал | каноны, SCSS, handoff | team-lead, developer |
| `product-tm/` | PTM | Система целиком | AS-IS→TO-BE→Bon→промпты N/M | owner GATE, designer |

## Поток

```text
Владелец → team-lead → documentarian (ТЗ/overview)
              ↓
         designer / product-tm (spec)
              ↓
         developer → tester
              ↓
    code-reviewer · outcome-ux (по запросу)
              ↓
         devops · cybersecurity
              ↓
    scout ← CODE_CHANGE_BOARD
```

## Правило одного исполнителя

Один `CURRENT_TASK.md` — один основной исполнитель.

## Доска кода

[CODE_CHANGE_BOARD.md](CODE_CHANGE_BOARD.md) → обрабатывает **scout** → `{{TECH_OVERVIEW_PATH}}/` → архив → очистка.
