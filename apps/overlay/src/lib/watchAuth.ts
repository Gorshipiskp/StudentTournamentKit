/** Commentator watch — invite resolve + redeem + TURN. */

export type RedeemResult = {
  access_token: string;
  match_id: string;
  role: string;
  caps: string[];
  expires_at: string;
};

export type TurnCredentials = {
  urls: string[];
  username: string;
  credential: string;
  ttl: number;
  expires_at: string;
};

/**
 * Invite raw token from `/watch/{token}` or `?token=` / `?invite=`.
 * Path token is preferred when present and not a reserved segment.
 */
export function resolveWatchInviteToken(pathname: string, search: string): string | null {
  const q = new URLSearchParams(search);
  const fromQuery = (q.get('token') || q.get('invite') || '').trim();
  if (fromQuery) return fromQuery;

  const m = pathname.match(/\/watch\/([^/?#]+)/i);
  if (m?.[1]) {
    const seg = decodeURIComponent(m[1]).trim();
    if (seg && seg.toLowerCase() !== 'index.html') return seg;
  }
  return null;
}

export function isWatchPath(pathname: string): boolean {
  return /\/watch(\/|$)/i.test(pathname);
}

export function isMockWatch(search: string): boolean {
  const q = new URLSearchParams(search);
  return q.get('mock') === '1' || q.get('mock') === 'true';
}

async function api<T>(
  path: string,
  init?: RequestInit & { accessToken?: string },
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (init?.accessToken) {
    headers.Authorization = `Bearer ${init.accessToken}`;
  }
  const { accessToken: _a, ...rest } = init || {};
  const res = await fetch(path, { ...rest, headers });
  if (!res.ok) {
    let detail = await res.text();
    try {
      const j = JSON.parse(detail) as { detail?: string };
      if (j.detail) detail = j.detail;
    } catch {
      /* keep */
    }
    throw new Error(detail || `${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function redeemInvite(token: string) {
  return api<RedeemResult>('/api/v1/invites/redeem', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
}

export function fetchTurnCredentials(matchId: string, accessToken: string) {
  return api<TurnCredentials>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/turn-credentials`,
    { method: 'POST', accessToken },
  );
}

export function bannerLabel(banner: string | null | undefined): string | null {
  if (!banner) return null;
  switch (banner) {
    case 'review_requested':
      return 'Запрошена проверка судьи';
    case 'pause_pending':
      return 'Готовится техническая пауза';
    case 'tech_pause':
      return 'Техническая пауза';
    default:
      return banner;
  }
}

/** Architectural limit: Platform allows max 2 concurrent /watch signaling subscribers. */
export const MAX_WATCH_SUBSCRIBERS = 2;
