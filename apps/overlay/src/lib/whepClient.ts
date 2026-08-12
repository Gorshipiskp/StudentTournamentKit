/** WHEP subscriber for MediaMTX (protocol 2 live). */

export type WhepStatus =
  | 'connecting'
  | 'waiting_publisher'
  | 'negotiating'
  | 'live'
  | 'closed'
  | 'error';

export type WhepHandles = {
  close: () => void;
};

export type WhepPlayCredentials = {
  path: string;
  whep_url: string;
  bearer: string;
  ttl: number;
  expires_at: string;
};

type Opts = {
  credentials: WhepPlayCredentials;
  /** Retry when publisher not online yet (ms). */
  retryMs?: number;
  onStatus: (s: WhepStatus) => void;
  onStream: (stream: MediaStream) => void;
  onError: (message: string) => void;
};

function waitIceGathering(pc: RTCPeerConnection, timeoutMs = 2000): Promise<void> {
  if (pc.iceGatheringState === 'complete') return Promise.resolve();
  return new Promise((resolve) => {
    const t = window.setTimeout(resolve, timeoutMs);
    pc.addEventListener('icegatheringstatechange', () => {
      if (pc.iceGatheringState === 'complete') {
        window.clearTimeout(t);
        resolve();
      }
    });
  });
}

/** True when MediaMTX has no publisher / path not ready yet. */
export function isPublisherMissingStatus(status: number, body: string): boolean {
  if (status === 404 || status === 204) return true;
  const lower = body.toLowerCase();
  return (
    status === 400 &&
    (lower.includes('no stream') ||
      lower.includes('not ready') ||
      lower.includes('no one is publishing') ||
      lower.includes('path not found') ||
      lower.includes('"error"'))
  );
}

export function connectWhepPlayer(opts: Opts): WhepHandles {
  let closed = false;
  let pc: RTCPeerConnection | null = null;
  let resourceUrl: string | null = null;
  let retryTimer: number | null = null;
  const retryMs = opts.retryMs ?? 3000;

  const cleanupPc = async () => {
    if (resourceUrl) {
      try {
        await fetch(resourceUrl, { method: 'DELETE' });
      } catch {
        /* ignore */
      }
      resourceUrl = null;
    }
    try {
      pc?.close();
    } catch {
      /* ignore */
    }
    pc = null;
  };

  const scheduleRetry = () => {
    if (closed || retryTimer != null) return;
    opts.onStatus('waiting_publisher');
    retryTimer = window.setTimeout(() => {
      retryTimer = null;
      void attempt();
    }, retryMs);
  };

  const attempt = async () => {
    if (closed) return;
    opts.onStatus('connecting');
    await cleanupPc();

    pc = new RTCPeerConnection();
    pc.addTransceiver('video', { direction: 'recvonly' });
    // F4: no audio negotiated for commentary VoIP
    pc.ontrack = (ev) => {
      if (closed) return;
      const stream = ev.streams[0] ?? new MediaStream([ev.track]);
      opts.onStream(stream);
      opts.onStatus('live');
    };
    pc.onconnectionstatechange = () => {
      if (!pc || closed) return;
      if (pc.connectionState === 'failed') {
        opts.onError('WHEP соединение оборвалось');
        opts.onStatus('error');
        scheduleRetry();
      }
    };

    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await waitIceGathering(pc);
      if (closed || !pc.localDescription?.sdp) return;

      opts.onStatus('negotiating');
      const headers: Record<string, string> = {
        'Content-Type': 'application/sdp',
      };
      if (opts.credentials.bearer) {
        headers.Authorization = `Bearer ${opts.credentials.bearer}`;
      }
      const res = await fetch(opts.credentials.whep_url, {
        method: 'POST',
        headers,
        body: pc.localDescription.sdp,
      });
      const text = await res.text();
      if (!res.ok) {
        if (isPublisherMissingStatus(res.status, text)) {
          scheduleRetry();
          return;
        }
        opts.onError(`WHEP недоступен (${res.status})`);
        opts.onStatus('error');
        scheduleRetry();
        return;
      }

      const loc = res.headers.get('Location');
      if (loc) {
        resourceUrl = loc.startsWith('http')
          ? loc
          : new URL(loc, opts.credentials.whep_url).toString();
      }
      await pc.setRemoteDescription({ type: 'answer', sdp: text });
    } catch (e) {
      if (closed) return;
      const msg = e instanceof Error ? e.message : 'WHEP ошибка';
      opts.onError(msg);
      opts.onStatus('error');
      scheduleRetry();
    }
  };

  void attempt();

  return {
    close: () => {
      closed = true;
      if (retryTimer != null) {
        window.clearTimeout(retryTimer);
        retryTimer = null;
      }
      opts.onStatus('closed');
      void cleanupPc();
    },
  };
}
