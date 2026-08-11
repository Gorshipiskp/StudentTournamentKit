# Матрица ролей ИИ-команды

> Подробные IDENTITY: `workers/<slug>/IDENTITY.md`.  
> **Активные роли** (уровень M): team-lead, developer, tester, documentarian, devops.  
> Остальные строки — справочник; папки создаются по мере необходимости.

| Папка | Роль | Фокус | Типичные задачи | Эскалация |
|-------|------|-------|-----------------|-----------|
| `team-lead/` | Team Lead | Приоритеты, ТЗ, координация | Декомпозиция, спринт, runbook | Владелец; все роли |
| `developer/` | Developer | Фичи end-to-end | API, UI, интеграции, тесты в scope | tester, devops |
| `tester/` | QA | Приёмка, регрессия | Чеклисты ТЗ, verify, баг-репорты | developer, team-lead |
| `documentarian/` | Documentarian | Docs ↔ код | overview/, tasks/, PROJECT.md | team-lead, developer |
| `devops/` | DevOps | CI, Docker, деплой | verify, release, env schema | developer |
| `cybersecurity/` | Security | Угрозы, auth, секреты | Threat model, review RBAC | developer, devops |
| `optimizer/` | Optimizer | Качество без смены поведения | Рефакторинг, perf | developer, team-lead |
| `scout/` | Scout | tech-overview | doc_coverage, CODE_CHANGE_BOARD | documentarian, tester |
| `code-reviewer/` | Code Reviewer | Ревью diff | Findings, targeted tests | developer, team-lead |
| `outcome-ux/` | Outcome UX | Поток, ясность | AUDIT notes, идеи UX | team-lead, designer |
| `designer/` | Designer | Дизайн-система, визуал | каноны, handoff | team-lead, developer |
| `product-tm/` | PTM | Система целиком | AS-IS→TO-BE→промпты N/M | owner GATE, designer |
| `sales/` | Sales | КП, pitch | commercial drafts | team-lead, владелец |
| `smm/` | SMM | Посты, анонсы | TG/VK черновики | team-lead, documentarian |

## Поток (уровень M)

```text
Владелец → team-lead → documentarian (ТЗ/overview)
              ↓
         developer → tester
              ↓
         devops (деплой, инфра)
```

## Правило одного исполнителя

Один `CURRENT_TASK.md` — один основной исполнитель.

## Доска кода

[CODE_CHANGE_BOARD.md](CODE_CHANGE_BOARD.md) → обрабатывает **scout** (когда появится) → `tech-overview/` → архив → очистка.
