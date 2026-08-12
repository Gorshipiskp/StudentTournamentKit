/** Judge panel → Platform API (invite redeem + review actions). */

export type MatchPublic = {
  id: string;
  status: string;
  review_status: string;
  review_resolution: string | null;
  version: number;
  score: { team_a: number; team_b: number };
  round: number;
  map: string | null;
  phase: string | null;
  judge_banner: string | null;
  actual_paused: boolean;
  desired_paused: boolean;
};

export type RedeemResult = {
  access_token: string;
  token_type: string;
  invite_id: string;
  match_id: string;
  role: string;
  caps: string[];
  expires_at: string;
};

export type JudgeSession = {
  accessToken: string;
  matchId: string;
  role: string;
  caps: string[];
};

/** Invite raw token from `?token=` (or `?invite=`). */
export function resolveInviteToken(search: string): string | null {
  const q = new URLSearchParams(search);
  const raw = (q.get('token') || q.get('invite') || '').trim();
  return raw || null;
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
      /* keep text */
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

export function getMatch(matchId: string) {
  return api<MatchPublic>(`/api/v1/matches/${encodeURIComponent(matchId)}`);
}

export function requestReview(matchId: string, accessToken: string) {
  return api<MatchPublic>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/judge/review-request`,
    { method: 'POST', accessToken },
  );
}

export function cancelReview(matchId: string, accessToken: string) {
  return api<MatchPublic>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/judge/review-cancel`,
    { method: 'POST', accessToken },
  );
}

export function resolveReview(
  matchId: string,
  accessToken: string,
  body: { action: 'continue' | 'forfeit'; version: number; losing_team?: string },
) {
  return api<{ match: MatchPublic }>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/judge/review-resolve`,
    {
      method: 'POST',
      accessToken,
      body: JSON.stringify(body),
    },
  );
}

export function reviewStatusLabel(status: string): string {
  switch (status) {
    case 'none':
      return 'Проверки нет';
    case 'requested':
      return 'Проверка запрошена — ждём паузу';
    case 'pause_pending':
      return 'Пауза готовится';
    case 'paused':
      return 'Техническая пауза';
    case 'resolved':
      return 'Проверка завершена';
    case 'cancelled':
      return 'Проверка отменена';
    default:
      return status;
  }
}
