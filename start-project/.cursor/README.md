# Cursor: skills и rules

> При bootstrap скопируй в `.cursor/` корня репо.  
> Переименуй префикс skills: `{{PROJECT_SLUG}}-agent-start`, `{{PROJECT_SLUG}}-developer`, …

## Skills (минимум)

| Skill | Файл | Назначение |
|-------|------|------------|
| agent-start | `skills/agent-start/SKILL.md` | Онбординг L0/L1/L2 |
| prompt-runbook | `skills/prompt-runbook/SKILL.md` | Автор ранбуков N/M |
| _shared | `skills/_shared/WORKER-STANDARDS.md` | Стандарт всех ролей |

## Skills (добавлять по мере роста)

- `team-lead`, `developer`, `tester`, `scout`, `designer`, `product-tm`, `code-reviewer`, `outcome-ux`, …

## Rules

| Rule | Файл |
|------|------|
| Ясность языка | `rules/clear-writing.mdc` |
| Токены | `rules/token-hygiene.mdc` |

## Подключение в Cursor

Rules с `alwaysApply: true` для token-hygiene и clear-writing — рекомендуется.
