# Student Tournament Platform — hub проекта

> Платформа для дистанционных CS2-турниров с полупрофессиональной трансляцией.  
> Репозиторий: `BestCSTournaments`.

---

## Быстрый старт

1. [overview/product.md](overview/product.md) — что строим
2. [docs/VISION.md](docs/VISION.md) — согласованное видение (полный лог калибровки)
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — техническая архитектура
4. [docs/ROADMAP.md](docs/ROADMAP.md) — этапы поставки
5. [AGENTS.md](AGENTS.md) — ИИ-команда в Cursor
6. [workers/sprint/CURRENT.md](workers/sprint/CURRENT.md) — активный спринт

---

## Профиль проекта

```yaml
project_name: Student Tournament Platform
short_name: STP
repo_slug: BestCSTournaments
owner: "<уточнить>"
primary_stack: "Python FastAPI + Svelte 5/SvelteKit + Go Director Agent + MySQL 8 + MatchZy/CSS"
team_scale: M
approach: vertical slices (not MVP stubs)
first_game: CS2 only
packages:
  - path: apps/api/
    role: backend
  - path: apps/overlay/
    role: broadcast overlay (Svelte)
  - path: apps/dashboard/
    role: director + organizer UI (Svelte)
  - path: apps/judge/
    role: judge mobile web (Svelte)
  - path: apps/director-agent/
    role: local OBS + WebRTC bridge (Windows)
  - path: infra/
    role: platform + game-server deploy
secrets_location: config/secrets/ — НЕ в workers/
verify_command: TBD (scripts/verify.ps1)
```

---

## Инфраструктура (кратко)

| Компонент | Где |
|-----------|-----|
| MySQL | Постоянный VPS организатора |
| Platform STP | Временный VPS на турнир |
| CS2 server | Временный VPS на турнир |
| OBS + CS2 + Director Agent | Ноутбук режиссёра |

---

## Команда (уровень M)

| Роль | Папка |
|------|-------|
| Team Lead | `workers/team-lead/` |
| Developer | `workers/developer/` |
| Tester | `workers/tester/` |
| Documentarian | `workers/documentarian/` |
| DevOps | `workers/devops/` |

---

## Документация

| Раздел | Путь |
|--------|------|
| Продукт | [overview/](overview/README.md) |
| Видение (калибровка) | [docs/VISION.md](docs/VISION.md) |
| **Домены и слои** | [docs/LAYERS.md](docs/LAYERS.md) |
| **Инварианты / reconciliation** | [docs/INVARIANTS.md](docs/INVARIANTS.md) |
| Архитектура | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) **v2.1** |
| **Технологический стек** | [docs/TECH-STACK.md](docs/TECH-STACK.md) |
| Решения (ADR) | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Roadmap | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Исходный brief | [docs/TECH-LEAD-BRIEF.md](docs/TECH-LEAD-BRIEF.md) |
| ТЗ | [tasks/](tasks/README.md) |

---

## Активный спринт

**S002** — Документация видения зафиксирована → следующий эпик: Foundation / Game Slice.  
[workers/sprint/CURRENT.md](workers/sprint/CURRENT.md)

---

## Секреты и git

- Секреты в `config/secrets/` — в `.gitignore`
- Коммиты — только по @owner
