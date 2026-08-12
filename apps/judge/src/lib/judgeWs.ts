/** Judge panel WebSocket — match.status push. */

import type { MatchPublic } from './api';

export type MatchStatusMessage = {
  protocol: number;
  type: 'match.status';
  match_id: string;
  reason: string;
  match: MatchPublic;
};

export type JudgeWsHandles = {
  close: () => void;
};

function buildJudgeWsUrl(matchId: string, accessToken: string, loc: Location = window.location): string {
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  const base = (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_WS_BASE;
  const root = base ? base.replace(/\/$/, '') : `${proto}//${loc.host}`;
  const q = new URLSearchParams({ token: accessToken });
  return `${root}/ws/judge/${encodeURIComponent(matchId)}?${q.toString()}`;
}

export function connectJudgeWs(
  matchId: string,
  accessToken: string,
  handlers: {
    onStatus: (m: MatchPublic, reason: string) => void;
    onError?: (msg: string) => void;
  },
): JudgeWsHandles {
  let closed = false;
  let timer: number | undefined;
  let ws: WebSocket | null = null;
  let attempt = 0;

  const connect = () => {
    if (closed) return;
    const url = buildJudgeWsUrl(matchId, accessToken);
    ws = new WebSocket(url);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(String(ev.data)) as MatchStatusMessage;
        if (msg.type === 'match.status' && msg.match) {
          handlers.onStatus(msg.match, msg.reason || 'update');
          attempt = 0;
        }
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      if (closed) return;
      attempt += 1;
      const delay = Math.min(8000, 500 * 2 ** Math.min(attempt, 4));
      timer = window.setTimeout(connect, delay);
    };
    ws.onerror = () => {
      handlers.onError?.('WS статус недоступен — опрос HTTP');
    };
  };

  connect();

  return {
    close: () => {
      closed = true;
      if (timer) window.clearTimeout(timer);
      try {
        ws?.close();
      } catch {
        /* ignore */
      }
      ws = null;
    },
  };
}
