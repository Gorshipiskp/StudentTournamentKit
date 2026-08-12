/** Client helpers to build overlay FX payloads (mirrors API live_fx kinds). */

import type { OverlayData, OverlayFx, OverlaySnapshot } from './snapshot';

export type LabFxKind =
  | 'round_win'
  | 'bomb_planted'
  | 'bomb_defusing'
  | 'bomb_defused'
  | 'bomb_exploded';

let seqCounter = 1000;

export function nextLabSeq(): number {
  seqCounter += 1;
  return seqCounter;
}

export function buildLabFx(
  kind: LabFxKind,
  opts: {
    side?: 'team_a' | 'team_b';
    site?: number;
    round?: number;
    timer_sec?: number;
    has_kit?: boolean;
  } = {},
): OverlayFx {
  const seq = nextLabSeq();
  const at = new Date().toISOString();
  const base = { at, seq, kind, label: '', ttl_ms: 4500 };

  switch (kind) {
    case 'round_win': {
      const side = opts.side ?? 'team_a';
      return {
        ...base,
        kind: 'round_win',
        side,
        round: opts.round ?? 3,
        ttl_ms: 7500,
        label: side === 'team_a' ? 'Победа CT' : 'Победа T',
      };
    }
    case 'bomb_planted':
      return {
        ...base,
        kind: 'bomb_planted',
        label: 'Бомба заложена',
        site: opts.site ?? 1,
        timer_sec: opts.timer_sec ?? 40,
        ttl_ms: 12_000,
      };
    case 'bomb_defusing':
      return {
        ...base,
        kind: 'bomb_defusing',
        label: 'Дефьюз',
        has_kit: opts.has_kit ?? true,
        ttl_ms: 8_000,
      };
    case 'bomb_defused':
      return {
        ...base,
        kind: 'bomb_defused',
        label: 'Бомба разминирована',
        ttl_ms: 5_000,
      };
    case 'bomb_exploded':
      return {
        ...base,
        kind: 'bomb_exploded',
        label: 'Взрыв',
        ttl_ms: 5_000,
      };
  }
}

export function emptyLabSnapshot(matchId = 'lab'): OverlaySnapshot {
  const data: OverlayData = {
    scene: 'ingame',
    team_a: { name: 'Team A', score: 4 },
    team_b: { name: 'Team B', score: 3 },
    map: 'de_mirage',
    round: 8,
    phase: 'live',
    match_status: 'live',
    paused: false,
    judge: { status: 'none', banner: null },
    watermark: { text: 'STP', visible: true },
    tournament_name: 'Overlay Lab',
    fx: null,
  };
  return {
    protocol: 1,
    type: 'overlay.snapshot',
    match_id: matchId,
    version: 1,
    data,
  };
}

export async function postOverlayFx(
  matchId: string,
  body: Record<string, string | number | boolean | null>,
): Promise<OverlaySnapshot> {
  const res = await fetch(`/api/v1/matches/${encodeURIComponent(matchId)}/overlay/fx`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as OverlaySnapshot;
}

export async function postOverlayOverride(
  matchId: string,
  body: Record<string, string | number | boolean | null>,
): Promise<OverlaySnapshot> {
  const res = await fetch(
    `/api/v1/matches/${encodeURIComponent(matchId)}/overlay/override`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as OverlaySnapshot;
}

export async function patchOverlayScene(
  matchId: string,
  desired_scene: string,
): Promise<void> {
  const res = await fetch(
    `/api/v1/matches/${encodeURIComponent(matchId)}/production`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ desired_scene }),
    },
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
}
