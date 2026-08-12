/** Organizer + director API client. */

export type MatchPublic = {
  id: string;
  status: string;
  score: { team_a: number; team_b: number };
  round: number;
  map: string | null;
  phase: string | null;
  judge_banner: string | null;
  actual_paused: boolean;
};

export type ProductionPublic = {
  match_id: string;
  desired: { scene: string; stream: string };
  actual: { scene: string | null; stream: string };
  agent_status: string;
  obs_status: string;
  broadcast_status: string;
};

export type OverlaySnapshot = {
  version: number;
  data: {
    scene: string;
    team_a: { name: string; score: number };
    team_b: { name: string; score: number };
  };
};

export type TournamentPublic = {
  id: string;
  name: string;
  format: string;
  status: string;
  settings: Record<string, unknown>;
};

export type PlayerPublic = {
  id: string;
  team_id: string;
  nickname: string;
  steam_id: string | null;
  is_coach: boolean;
};

export type TeamPublic = {
  id: string;
  tournament_id: string;
  name: string;
  tag: string;
  players: PlayerPublic[];
};

export type BracketNodePublic = {
  id: string;
  tournament_id: string;
  round: number;
  position: number;
  team_a_id: string | null;
  team_b_id: string | null;
  source_a_node_id: string | null;
  source_b_node_id: string | null;
  match_id: string | null;
};

export type BrandingPublic = {
  tournament_id: string;
  colors: Record<string, unknown>;
  has_logo: boolean;
  has_bg: boolean;
  logo_content_type: string | null;
  bg_content_type: string | null;
};

const SCENES = ['waiting', 'intro', 'teams', 'ingame', 'break', 'winner'] as const;
export type SceneId = (typeof SCENES)[number];
export { SCENES };

const TOKEN_KEY = 'stk_organizer_token';

export function getOrganizerToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setOrganizerToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function resolveMatchId(pathname: string, search: string): string | null {
  const q = new URLSearchParams(search).get('matchId');
  if (q?.trim()) return q.trim();
  const m = pathname.match(/\/director\/([^/?#]+)/i);
  return m?.[1] ? decodeURIComponent(m[1]) : null;
}

export function isAdminPath(pathname: string): boolean {
  return /^\/admin(?:\/|$)/i.test(pathname);
}

export function resolveAdminTournamentId(pathname: string): string | null {
  const m = pathname.match(/\/admin\/tournaments\/([^/?#]+)/i);
  return m?.[1] ? decodeURIComponent(m[1]) : null;
}

export function isAdminBracketPath(pathname: string): boolean {
  return /\/admin\/tournaments\/[^/?#]+\/bracket\/?$/i.test(pathname);
}

export function isAdminBrandingPath(pathname: string): boolean {
  return /\/admin\/tournaments\/[^/?#]+\/branding\/?$/i.test(pathname);
}

async function api<T>(
  path: string,
  init?: RequestInit & { token?: string | null },
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  };
  const token = init?.token ?? getOrganizerToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const { token: _t, ...rest } = init || {};
  const res = await fetch(path, { ...rest, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function loginOrganizer(username: string, password: string) {
  return api<{
    access_token: string;
    token_type: string;
    role: string;
    expires_at: string;
  }>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    token: null,
  });
}

export function listTournaments() {
  return api<{ items: TournamentPublic[] }>('/api/v1/tournaments');
}

export function createTournament(body: {
  name: string;
  format?: string;
  settings?: Record<string, unknown>;
}) {
  return api<TournamentPublic>('/api/v1/tournaments', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function publishTournament(tournamentId: string) {
  return api<TournamentPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/publish`,
    { method: 'POST' },
  );
}

export function getTournament(tournamentId: string) {
  return api<TournamentPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}`,
  );
}

export function listTeams(tournamentId: string) {
  return api<{ items: TeamPublic[] }>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams`,
  );
}

export function createTeam(
  tournamentId: string,
  body: { name: string; tag?: string },
) {
  return api<TeamPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams`,
    { method: 'POST', body: JSON.stringify(body) },
  );
}

export function patchTeam(
  tournamentId: string,
  teamId: string,
  body: { name?: string; tag?: string },
) {
  return api<TeamPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams/${encodeURIComponent(teamId)}`,
    { method: 'PATCH', body: JSON.stringify(body) },
  );
}

export function deleteTeam(tournamentId: string, teamId: string) {
  return api<{ ok: boolean }>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams/${encodeURIComponent(teamId)}`,
    { method: 'DELETE' },
  );
}

export function createPlayer(
  tournamentId: string,
  teamId: string,
  body: { nickname: string; steam_id?: string | null; is_coach?: boolean },
) {
  return api<PlayerPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams/${encodeURIComponent(teamId)}/players`,
    { method: 'POST', body: JSON.stringify(body) },
  );
}

export function deletePlayer(
  tournamentId: string,
  teamId: string,
  playerId: string,
) {
  return api<{ ok: boolean }>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/teams/${encodeURIComponent(teamId)}/players/${encodeURIComponent(playerId)}`,
    { method: 'DELETE' },
  );
}

export function getBracket(tournamentId: string) {
  return api<{ items: BracketNodePublic[] }>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/bracket`,
  );
}

export function generateBracket(
  tournamentId: string,
  body: { size: number; replace?: boolean },
) {
  return api<{ items: BracketNodePublic[] }>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/bracket/generate?size=${body.size}`,
    {
      method: 'POST',
      body: JSON.stringify({ size: body.size, replace: body.replace ?? false }),
    },
  );
}

export function assignBracketNode(
  tournamentId: string,
  nodeId: string,
  body: {
    team_a_id?: string | null;
    team_b_id?: string | null;
    clear_team_a?: boolean;
    clear_team_b?: boolean;
  },
) {
  return api<BracketNodePublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/bracket/nodes/${encodeURIComponent(nodeId)}`,
    { method: 'PATCH', body: JSON.stringify(body) },
  );
}

export type StaffLinks = {
  match_id: string;
  director_url: string;
  judge: { invite_id: string; token: string; url: string; role: string };
  commentator: { invite_id: string; token: string; url: string; role: string };
};

export function startMatch(matchId: string) {
  return api<{
    match: { id: string; status: string; phase: string | null };
    mode: string;
    note: string;
    already_live: boolean;
  }>(`/api/v1/matches/${encodeURIComponent(matchId)}/start`, {
    method: 'POST',
  });
}

export function createStaffLinks(matchId: string) {
  return api<StaffLinks>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/staff-links`,
    { method: 'POST' },
  );
}

export function getMatchPublic(matchId: string) {
  return api<{ id: string; status: string; phase: string | null }>(
    `/api/v1/matches/${encodeURIComponent(matchId)}`,
    { token: null },
  );
}

export function getBranding(tournamentId: string) {
  return api<BrandingPublic>(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/branding`,
  );
}

export async function uploadBranding(
  tournamentId: string,
  opts: {
    colors?: Record<string, string>;
    logo?: File | null;
    clearLogo?: boolean;
  },
): Promise<BrandingPublic> {
  const form = new FormData();
  if (opts.colors) form.append('colors', JSON.stringify(opts.colors));
  if (opts.logo) form.append('logo', opts.logo);
  if (opts.clearLogo) form.append('clear_logo', 'true');
  const token = getOrganizerToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(
    `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/branding`,
    { method: 'PUT', body: form, headers },
  );
  if (!res.ok) {
    throw new Error(`${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<BrandingPublic>;
}

export function getMatch(matchId: string) {
  return api<MatchPublic>(`/api/v1/matches/${encodeURIComponent(matchId)}`, {
    token: null,
  });
}

export function getProduction(matchId: string) {
  return api<ProductionPublic>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/production`,
    { token: null },
  );
}

export function getOverlay(matchId: string) {
  return api<OverlaySnapshot>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/overlay`,
    { token: null },
  );
}

export function patchScene(matchId: string, desired_scene: SceneId) {
  return api<ProductionPublic>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/production`,
    {
      method: 'PATCH',
      body: JSON.stringify({ desired_scene }),
      token: null,
    },
  );
}

export function postOverride(
  matchId: string,
  body: Record<string, string | number | boolean | null>,
) {
  return api<OverlaySnapshot>(
    `/api/v1/matches/${encodeURIComponent(matchId)}/overlay/override`,
    {
      method: 'POST',
      body: JSON.stringify(body),
      token: null,
    },
  );
}
