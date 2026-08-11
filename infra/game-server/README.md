# infra/game-server — операторский runbook (CS2 VPS)

Контракт: [CONTRACT.md](./CONTRACT.md) · Bridge: [plugins/STK.Bridge/](./plugins/STK.Bridge/) · Fake (без VPS): `tools/fake-cs2/`.

**live deploy:** только с доступом @owner (SSH). Локально всегда начинай с dry-run.

---

## Быстрый путь без VPS

1. Platform: compose + migrate (TZ001).
2. `tools/fake-cs2` → events/commands.
3. Durable demo stub: Platform пишет в `data/demos/{match_id}/` при `match_completed` (ADR-034).

---

## Установка на Ubuntu VPS

```bash
# с машины разработчика / на VPS после git clone
./scripts/deploy-cs2.sh --dry-run
sudo ./scripts/deploy-cs2.sh --yes   # SteamCMD + apt scaffolding; остальное — по чеклисту ниже
```

Windows-хелпер (только план): `.\scripts\deploy-cs2.ps1`

### Чеклист

| # | Шаг | Примечание |
|---|-----|------------|
| 1 | SteamCMD + `app_update 730` | CS2 Dedicated |
| 2 | Metamod:Source | актуальный билд под CS2 |
| 3 | CounterStrikeSharp | https://docs.cssharp.dev/ |
| 4 | MatchZy | **не fork** (F1); https://github.com/shobhit-pathak/MatchZy |
| 5 | STK.Bridge | `dotnet build` на машине с SDK → `addons/counterstrikesharp/plugins/STK.Bridge/` |
| 6 | `config.json` Bridge | PlatformUrl, WebhookSecret, MatchId, ServerId, CommandListenPort |
| 7 | Firewall | 27015 game, 27020 GOTV; command port **только** с Platform |
| 8 | Register | `POST /api/v1/game-servers` + `POST /api/v1/matches/{id}/assign-server` |
| 9 | GOTV | `tv_enable 1`, `tv_autorecord 1` |
| 10 | Demo durable | после матча Platform копирует/создаёт запись в `demo_files` → затем можно teardown CS2 |

---

## Register hint

```bash
export PLATFORM_URL=http://<platform-host>:8000
export CS2_WEBHOOK_SECRET=...
export STK_SERVER_ID=srv_1

curl -sS -X POST "$PLATFORM_URL/api/v1/game-servers" \
  -H 'Content-Type: application/json' \
  -d "{\"server_id\":\"$STK_SERVER_ID\",\"endpoint_url\":\"http://<cs2-ip>:27099\",\"webhook_secret\":\"$CS2_WEBHOOK_SECRET\",\"host\":\"<cs2-ip>\",\"port\":27015}"

curl -sS -X POST "$PLATFORM_URL/api/v1/matches/<match_id>/assign-server" \
  -H 'Content-Type: application/json' \
  -d "{\"server_id\":\"$STK_SERVER_ID\"}"
```

---

## Demo lifecycle (ADR-034)

```text
match ends on CS2/Fake
  → ephemeral .dem on game disk (or Fake stub file)
  → Platform finalize → data/demos/{match_id}/*.dem
  → demo_files.durable_uri points to durable path
  → CS2 VPS may be destroyed
```

Запрещено считать демо «сохранённым», пока файл только на ephemeral CS2.

Env: `DEMO_DURABLE_ROOT` (по умолчанию `data/demos` от корня репо / cwd API).

---

## Статус

| Компонент | Состояние |
|-----------|-----------|
| CONTRACT + Fake | working |
| Bridge skeleton | в репо; build может быть blocked без SDK |
| deploy-cs2.sh | dry-run + scaffolding; полный Steam/CSS — оператор на VPS |
| live_smoke | **blocked** без SSH/@owner |
