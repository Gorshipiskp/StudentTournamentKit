import { parseOverlaySnapshot, type OverlaySnapshot } from './snapshot';

export type OverlayWsHandlers = {
  onSnapshot: (snap: OverlaySnapshot) => void;
  onStatus: (status: 'connecting' | 'open' | 'closed' | 'error') => void;
};

/**
 * Connect to Platform overlay WS.
 * Full snapshot on every message; reconnect with backoff (client state discarded).
 */
export function connectOverlayWs(
  url: string,
  handlers: OverlayWsHandlers,
): { close: () => void } {
  let socket: WebSocket | null = null;
  let closedByUser = false;
  let attempt = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const clearTimer = () => {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  };

  const scheduleReconnect = () => {
    if (closedByUser) return;
    const delay = Math.min(8000, 500 * 2 ** attempt);
    attempt += 1;
    clearTimer();
    timer = setTimeout(open, delay);
  };

  const open = () => {
    handlers.onStatus('connecting');
    try {
      socket = new WebSocket(url);
    } catch {
      handlers.onStatus('error');
      scheduleReconnect();
      return;
    }

    socket.addEventListener('open', () => {
      attempt = 0;
      handlers.onStatus('open');
    });

    socket.addEventListener('message', (ev) => {
      try {
        const raw = typeof ev.data === 'string' ? JSON.parse(ev.data) : ev.data;
        const snap = parseOverlaySnapshot(raw);
        handlers.onSnapshot(snap);
      } catch {
        // ignore malformed frames; wait for next full snapshot
      }
    });

    socket.addEventListener('close', () => {
      handlers.onStatus('closed');
      scheduleReconnect();
    });

    socket.addEventListener('error', () => {
      handlers.onStatus('error');
    });
  };

  open();

  return {
    close: () => {
      closedByUser = true;
      clearTimer();
      socket?.close();
      socket = null;
    },
  };
}
