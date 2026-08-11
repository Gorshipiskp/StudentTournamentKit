# scripts/

| Скрипт | Назначение |
|--------|------------|
| `verify.ps1` | Локальная проверка: compose config + pytest |
| `verify.sh` | То же для bash |
| `deploy-cs2.sh` | CS2 VPS install path (SteamCMD/CSS/MatchZy/Bridge) — **`--dry-run` по умолчанию** |
| `deploy-cs2.ps1` | Windows-хелпер: печатает план / вызывает bash dry-run |

Операторский runbook: `infra/game-server/README.md`.  
Live SSH-деплой — только @owner.
