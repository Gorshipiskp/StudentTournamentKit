/** Overlay snapshot types + parse (contract v1). */

export type OverlayTeam = {
  name: string;
  score: number;
};

export type OverlayFx = {
  kind: string;
  at: string;
  ttl_ms: number;
  seq: number;
  label: string;
  side?: string | null;
  site?: string | number | null;
  timer_sec?: number | null;
  has_kit?: boolean;
  reason?: string | null;
  round?: number | null;
};

export type OverlayData = {
  scene: string;
  team_a: OverlayTeam;
  team_b: OverlayTeam;
  map: string | null;
  round: number;
  phase: string | null;
  match_status: string | null;
  paused: boolean;
  judge: { status: string; banner: string | null };
  watermark: { text: string; visible: boolean };
  tournament_name?: string | null;
  branding?: {
    logo_url: string | null;
    bg_url: string | null;
    colors: Record<string, string>;
  };
  fx?: OverlayFx | null;
};

export type OverlaySnapshot = {
  protocol: number;
  type: 'overlay.snapshot';
  match_id: string;
  version: number;
  data: OverlayData;
};

export class SnapshotParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SnapshotParseError';
  }
}

function asRecord(value: unknown, label: string): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new SnapshotParseError(`${label} must be object`);
  }
  return value as Record<string, unknown>;
}

function asTeam(value: unknown, label: string): OverlayTeam {
  const t = asRecord(value, label);
  return {
    name: typeof t.name === 'string' ? t.name : 'Team',
    score: typeof t.score === 'number' ? t.score : Number(t.score) || 0,
  };
}

/** Parse WS/HTTP overlay.snapshot; rejects wrong type/protocol. */
export function parseOverlaySnapshot(raw: unknown): OverlaySnapshot {
  const msg = asRecord(raw, 'snapshot');
  if (msg.type !== 'overlay.snapshot') {
    throw new SnapshotParseError(`unexpected type: ${String(msg.type)}`);
  }
  const protocol = Number(msg.protocol);
  if (!Number.isFinite(protocol) || protocol < 1) {
    throw new SnapshotParseError('invalid protocol');
  }
  const version = Number(msg.version);
  if (!Number.isFinite(version) || version < 1) {
    throw new SnapshotParseError('invalid version');
  }
  const matchId = typeof msg.match_id === 'string' ? msg.match_id : '';
  const dataRaw = asRecord(msg.data, 'data');
  const judgeRaw = asRecord(dataRaw.judge ?? { status: 'none', banner: null }, 'judge');
  const watermarkRaw = asRecord(
    dataRaw.watermark ?? { text: 'STP', visible: true },
    'watermark',
  );

  let branding: OverlayData['branding'];
  if (dataRaw.branding && typeof dataRaw.branding === 'object' && !Array.isArray(dataRaw.branding)) {
    const b = dataRaw.branding as Record<string, unknown>;
    const colorsRaw =
      b.colors && typeof b.colors === 'object' && !Array.isArray(b.colors)
        ? (b.colors as Record<string, unknown>)
        : {};
    const colors: Record<string, string> = {};
    for (const [k, v] of Object.entries(colorsRaw)) {
      if (typeof v === 'string') colors[k] = v;
    }
    branding = {
      logo_url: typeof b.logo_url === 'string' ? b.logo_url : null,
      bg_url: typeof b.bg_url === 'string' ? b.bg_url : null,
      colors,
    };
  }

  let fx: OverlayFx | null = null;
  if (dataRaw.fx && typeof dataRaw.fx === 'object' && !Array.isArray(dataRaw.fx)) {
    const f = dataRaw.fx as Record<string, unknown>;
    if (typeof f.kind === 'string' && typeof f.label === 'string') {
      fx = {
        kind: f.kind,
        at: typeof f.at === 'string' ? f.at : new Date().toISOString(),
        ttl_ms: typeof f.ttl_ms === 'number' ? f.ttl_ms : Number(f.ttl_ms) || 4000,
        seq: typeof f.seq === 'number' ? f.seq : Number(f.seq) || 0,
        label: f.label,
        side: typeof f.side === 'string' ? f.side : null,
        site: typeof f.site === 'string' || typeof f.site === 'number' ? f.site : null,
        timer_sec:
          typeof f.timer_sec === 'number' ? f.timer_sec : f.timer_sec != null ? Number(f.timer_sec) : null,
        has_kit: Boolean(f.has_kit),
        reason: typeof f.reason === 'string' ? f.reason : null,
        round: typeof f.round === 'number' ? f.round : null,
      };
    }
  }

  return {
    protocol,
    type: 'overlay.snapshot',
    match_id: matchId,
    version,
    data: {
      scene: typeof dataRaw.scene === 'string' ? dataRaw.scene : 'waiting',
      team_a: asTeam(dataRaw.team_a ?? { name: 'Team A', score: 0 }, 'team_a'),
      team_b: asTeam(dataRaw.team_b ?? { name: 'Team B', score: 0 }, 'team_b'),
      map: typeof dataRaw.map === 'string' ? dataRaw.map : null,
      round: typeof dataRaw.round === 'number' ? dataRaw.round : Number(dataRaw.round) || 0,
      phase: typeof dataRaw.phase === 'string' ? dataRaw.phase : null,
      match_status: typeof dataRaw.match_status === 'string' ? dataRaw.match_status : null,
      paused: Boolean(dataRaw.paused),
      judge: {
        status: typeof judgeRaw.status === 'string' ? judgeRaw.status : 'none',
        banner: typeof judgeRaw.banner === 'string' ? judgeRaw.banner : null,
      },
      // F4: watermark always treated as visible in UI even if server omits flag
      watermark: {
        text: typeof watermarkRaw.text === 'string' ? watermarkRaw.text : 'STP',
        visible: true,
      },
      tournament_name:
        typeof dataRaw.tournament_name === 'string' ? dataRaw.tournament_name : null,
      branding,
      fx,
    },
  };
}

/** Minimal snapshot for UI before first WS frame or when snapshot is missing. */
export function emptyOverlaySnapshot(matchId = ''): OverlaySnapshot {
  return {
    protocol: 1,
    type: 'overlay.snapshot',
    match_id: matchId,
    version: 0,
    data: {
      scene: 'waiting',
      team_a: { name: 'Team A', score: 0 },
      team_b: { name: 'Team B', score: 0 },
      map: null,
      round: 0,
      phase: null,
      match_status: null,
      paused: false,
      judge: { status: 'none', banner: null },
      watermark: { text: 'STP', visible: true },
    },
  };
}

/** Extract match id from `/overlay/{matchId}` or `?matchId=`. */
export function resolveMatchId(pathname: string, search: string): string | null {
  const fromQuery = new URLSearchParams(search).get('matchId');
  if (fromQuery && fromQuery.trim()) {
    return fromQuery.trim();
  }
  const m = pathname.match(/\/overlay\/([^/?#]+)/i);
  if (m?.[1]) {
    return decodeURIComponent(m[1]);
  }
  return null;
}

export function buildOverlayWsUrl(matchId: string, loc: Location = window.location): string {
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  // Same-origin (vite proxy / nginx) unless VITE_WS_BASE set
  const base = (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_WS_BASE;
  if (base) {
    return `${base.replace(/\/$/, '')}/ws/overlay/${encodeURIComponent(matchId)}`;
  }
  return `${proto}//${loc.host}/ws/overlay/${encodeURIComponent(matchId)}`;
}
