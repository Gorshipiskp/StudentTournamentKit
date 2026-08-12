/** Canvas → MediaStream for mock /watch without Agent publisher (P4 DoD). */

export type MockStreamHandle = {
  stream: MediaStream;
  stop: () => void;
};

/** Synthetic color bars + timestamp; video-only (F7). */
export function createMockWatchStream(): MockStreamHandle {
  const canvas = document.createElement('canvas');
  canvas.width = 1280;
  canvas.height = 720;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('canvas 2d unavailable');
  }

  let raf = 0;
  const draw = () => {
    const t = performance.now() / 1000;
    const g = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    g.addColorStop(0, `hsl(${(t * 40) % 360} 45% 22%)`);
    g.addColorStop(1, `hsl(${(t * 40 + 80) % 360} 40% 14%)`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.font = 'bold 48px Segoe UI, sans-serif';
    ctx.fillText('STK mock эфир', 48, 120);
    ctx.font = '28px Segoe UI, sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.fillText('Нет Agent publisher — mock=1', 48, 170);
    ctx.fillText(new Date().toLocaleTimeString('ru-RU'), 48, 220);
    raf = requestAnimationFrame(draw);
  };
  draw();

  const stream = canvas.captureStream(30);
  return {
    stream,
    stop: () => {
      cancelAnimationFrame(raf);
      for (const track of stream.getTracks()) track.stop();
    },
  };
}
