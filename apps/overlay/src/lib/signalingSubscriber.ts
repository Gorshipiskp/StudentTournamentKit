/** WebRTC subscriber: Platform signaling → RTCPeerConnection (video-only). */

import type { TurnCredentials } from './watchAuth';

export type SubscriberStatus =
  | 'connecting'
  | 'waiting_offer'
  | 'negotiating'
  | 'live'
  | 'closed'
  | 'error';

export type SubscriberHandles = {
  close: () => void;
};

type Opts = {
  matchId: string;
  accessToken: string;
  turn?: TurnCredentials | null;
  onStatus: (s: SubscriberStatus) => void;
  onStream: (stream: MediaStream) => void;
  onError: (message: string) => void;
};

function buildSignalingUrl(matchId: string, accessToken: string, loc: Location = window.location): string {
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  const base = (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_WS_BASE;
  const root = base ? base.replace(/\/$/, '') : `${proto}//${loc.host}`;
  const q = new URLSearchParams({
    role: 'subscriber',
    token: accessToken,
  });
  return `${root}/ws/signaling/${encodeURIComponent(matchId)}?${q.toString()}`;
}

export function connectWatchSubscriber(opts: Opts): SubscriberHandles {
  let closed = false;
  let peerId: string | null = null;
  let pc: RTCPeerConnection | null = null;
  let ws: WebSocket | null = null;

  const iceServers: RTCIceServer[] = [{ urls: 'stun:stun.l.google.com:19302' }];
  if (opts.turn?.urls?.length) {
    iceServers.push({
      urls: opts.turn.urls,
      username: opts.turn.username,
      credential: opts.turn.credential,
    });
  }

  const send = (msg: Record<string, unknown>) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ protocol: 1, ...msg }));
    }
  };

  const ensurePc = () => {
    if (pc) return pc;
    pc = new RTCPeerConnection({ iceServers });
    pc.addTransceiver('video', { direction: 'recvonly' });
    // F7: no audio
    pc.ontrack = (ev) => {
      const stream = ev.streams[0] ?? new MediaStream([ev.track]);
      opts.onStream(stream);
      opts.onStatus('live');
    };
    pc.onicecandidate = (ev) => {
      if (!ev.candidate || !peerId) return;
      const remote = (pc as RTCPeerConnection & { _remotePeerId?: string })._remotePeerId;
      if (!remote) return;
      send({
        type: 'signaling.ice',
        from: peerId,
        to: remote,
        candidate: ev.candidate.toJSON(),
      });
    };
    pc.onconnectionstatechange = () => {
      if (!pc) return;
      if (pc.connectionState === 'failed') {
        opts.onError('WebRTC соединение оборвалось');
        opts.onStatus('error');
      }
    };
    return pc;
  };

  opts.onStatus('connecting');
  const url = buildSignalingUrl(opts.matchId, opts.accessToken);
  ws = new WebSocket(url);

  ws.onopen = () => {
    if (!closed) opts.onStatus('waiting_offer');
  };

  ws.onerror = () => {
    if (!closed) {
      opts.onError('Ошибка signaling WebSocket');
      opts.onStatus('error');
    }
  };

  ws.onclose = (ev) => {
    if (closed) return;
    if (ev.code === 4429) {
      opts.onError('Уже открыто максимум 2 вкладки комментатора');
    } else if (ev.code === 4401) {
      opts.onError('Нет доступа к эфиру (invite)');
    }
    opts.onStatus('closed');
  };

  ws.onmessage = async (ev) => {
    if (closed) return;
    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(String(ev.data)) as Record<string, unknown>;
    } catch {
      return;
    }
    const type = String(msg.type || '');
    if (type === 'signaling.hello') {
      peerId = String(msg.peer_id || '');
      opts.onStatus('waiting_offer');
      return;
    }
    if (type === 'error') {
      opts.onError(String(msg.detail || 'signaling error'));
      return;
    }
    if (type === 'signaling.offer') {
      const from = String(msg.from || '');
      const sdp = String(msg.sdp || '');
      if (!peerId || !sdp) return;
      opts.onStatus('negotiating');
      const conn = ensurePc();
      (conn as RTCPeerConnection & { _remotePeerId?: string })._remotePeerId = from;
      await conn.setRemoteDescription({ type: 'offer', sdp });
      const answer = await conn.createAnswer();
      await conn.setLocalDescription(answer);
      send({
        type: 'signaling.answer',
        from: peerId,
        to: from,
        sdp: answer.sdp,
      });
      return;
    }
    if (type === 'signaling.ice') {
      const cand = msg.candidate as RTCIceCandidateInit | undefined;
      if (!cand || !pc) return;
      try {
        await pc.addIceCandidate(cand);
      } catch {
        /* ignore late candidates */
      }
    }
  };

  return {
    close: () => {
      closed = true;
      opts.onStatus('closed');
      try {
        ws?.close();
      } catch {
        /* ignore */
      }
      ws = null;
      try {
        pc?.close();
      } catch {
        /* ignore */
      }
      pc = null;
    },
  };
}
