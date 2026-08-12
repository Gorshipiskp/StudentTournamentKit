/** Commentator watch — invite resolve + redeem + TURN / WHEP. */

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

export type WhepPlayCredentials = {
  path: string;
  whep_url: string;
  bearer: string;
  ttl: number;
  expires_at: string;
};

/** protocol 2 live | protocol 1 fake | local canvas */
export type MediaMode = 'whep' | 'fake' | 'mock';

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

/**
 * Resolve media bootstrap mode.
 * - `?mock=1` → mock
 * - `?media=fake|whep|mock` → explicit
 * - default → **whep** (TZ011 live canon); Fake rehearsals use `?media=fake`
 */
export function resolveMediaMode(search: string): MediaMode {
  if (isMockWatch(search)) return 'mock';
  const q = new URLSearchParams(search);
  const raw = (q.get('media') || '').trim().toLowerCase();
  if (raw === 'fake' || raw === 'whep' || raw === 'mock') return raw;
  const env = (import.meta as ImportMeta & { env?: Record<string, string> }).env
    ?.VITE_WATCH_MEDIA_MODE;
  if (env === 'fake' || env === 'whep' || env === 'mock') return env;
  return 'whep';
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

export function fetchWhepPlay(matchId: string, accessToken: string) {
  return api<WhepPlayCredentials>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/whep-play`,
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

/** Architectural limit: max 2 concurrent WHEP credentials / Fake signaling subscribers. */
export const MAX_WATCH_SUBSCRIBERS = 2;

export function humanWatchError(raw: string): string {
  const t = raw.trim();
  if (/401|unauthorized|invalid.?token|expired/i.test(t)) {
    return 'Ссылка устарела или уже использована. Попросите у организатора новую.';
  }
  if (/403|forbidden/i.test(t)) {
    return 'Нет доступа к эфиру. Нужна ссылка комментатора, не судьи.';
  }
  if (/429|too many|максимум 2|max(imum)?\s*2|whep limit/i.test(t)) {
    return 'Уже смотрят двое по разным ссылкам. Закройте лишнюю вкладку или попросите новую ссылку.';
  }
  if (/404/i.test(t)) {
    return 'Матч или эфир не найден. Проверьте ссылку у организатора.';
  }
  if (t.length > 180) return t.slice(0, 180) + '…';
  return t || 'Неизвестная ошибка';
}

export function mediaStatusLabel(status: string): string {
  switch (status) {
    case 'live':
    case 'mock':
      return 'В эфире';
    case 'waiting_offer':
    case 'waiting_publisher':
      return 'Ждём картинку';
    case 'connecting':
    case 'negotiating':
      return 'Подключаемся…';
    case 'closed':
      return 'Отключено';
    case 'error':
      return 'Ошибка';
    default:
      return status;
  }
}

export function mediaModeHint(mode: MediaMode): string | null {
  if (mode === 'fake') return 'Репетиция (тестовый канал)';
  if (mode === 'mock') return 'Демо-картинка';
  return null;
}

export function sceneLabel(scene: string | null | undefined): string {
  switch (scene) {
    case 'waiting':
      return 'Ожидание';
    case 'intro':
      return 'Интро';
    case 'teams':
      return 'Команды';
    case 'ingame':
      return 'Игра';
    case 'break':
      return 'Перерыв';
    case 'winner':
      return 'Победитель';
    default:
      return scene || '—';
  }
}
