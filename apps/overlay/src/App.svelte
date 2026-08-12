<script lang="ts">
  import type { OverlaySnapshot } from './lib/snapshot';
  import {
    buildOverlayWsUrl,
    parseOverlaySnapshot,
    resolveMatchId,
  } from './lib/snapshot';
  import { connectOverlayWs } from './lib/connectOverlayWs';
  import OverlayView from './lib/OverlayView.svelte';
  import OverlayLab from './lib/OverlayLab.svelte';
  import WatchPage from './lib/WatchPage.svelte';
  import {
    isWatchPath,
    resolveMediaMode,
    resolveWatchInviteToken,
    type MediaMode,
  } from './lib/watchAuth';
  import { onMount } from 'svelte';

  let mode = $state<'overlay' | 'watch' | 'lab' | 'boot'>('boot');
  let matchId = $state<string | null>(null);
  let watchToken = $state<string | null>(null);
  let watchMediaMode = $state<MediaMode>('whep');
  let snapshot = $state<OverlaySnapshot | null>(null);
  let status = $state<'connecting' | 'open' | 'closed' | 'error' | 'idle'>('idle');
  let error = $state<string | null>(null);

  function applySnapshot(snap: OverlaySnapshot) {
    // Ignore stale HTTP polls older than what WS already showed
    if (snapshot && snap.version < snapshot.version) return;
    snapshot = snap;
    error = null;
  }

  async function pullHttp(id: string) {
    try {
      const res = await fetch(`/api/v1/matches/${encodeURIComponent(id)}/overlay`);
      if (!res.ok) return;
      const raw: unknown = await res.json();
      applySnapshot(parseOverlaySnapshot(raw));
    } catch {
      // WS remains primary; poll is best-effort
    }
  }

  onMount(() => {
    const path = window.location.pathname;
    const search = window.location.search;

    if (path === '/overlay-lab' || path.startsWith('/overlay-lab/')) {
      mode = 'lab';
      return;
    }

    if (isWatchPath(path)) {
      const token = resolveWatchInviteToken(path, search);
      mode = 'watch';
      watchToken = token;
      watchMediaMode = resolveMediaMode(search);
      if (!token) {
        error = 'Откройте /watch?token=<invite> или /watch/<invite>';
      }
      return;
    }

    mode = 'overlay';
    const id = resolveMatchId(path, search);
    matchId = id;
    if (!id) {
      error = 'Укажите матч в URL: /overlay/{matchId} · или откройте /overlay-lab';
      return;
    }

    void pullHttp(id);

    const url = buildOverlayWsUrl(id);
    const session = connectOverlayWs(url, {
      onSnapshot: (snap) => {
        applySnapshot(snap);
      },
      onStatus: (s) => {
        status = s;
      },
    });

    // HTTP backup: OBS Browser Source often freezes WS when scene is hidden
    const poll = window.setInterval(() => {
      if (document.visibilityState === 'visible') void pullHttp(id);
    }, 1500);

    const onVisible = () => {
      if (document.visibilityState === 'visible') void pullHttp(id);
    };
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      session.close();
      window.clearInterval(poll);
      document.removeEventListener('visibilitychange', onVisible);
    };
  });
</script>

{#if mode === 'lab'}
  <OverlayLab />
{:else if mode === 'watch'}
  {#if error && !watchToken}
    <main class="watch-deny">
      <div class="card">
        <span class="mark">STK</span>
        <p class="eyebrow">Студенческий эфир</p>
        <h1>Комментатор</h1>
        <p>{error}</p>
        <p class="tip">
          Нужна ссылка «смотреть» от организатора (из блока «Ссылки для команды»).
        </p>
      </div>
    </main>
  {:else if watchToken}
    <WatchPage inviteToken={watchToken} mediaMode={watchMediaMode} />
  {/if}
{:else if error && !snapshot}
  <main class="boot">
    <div class="card">
      <span class="mark">STK</span>
      <p>{error}</p>
      <p class="tip"><a href="/overlay-lab">Лаборатория оверлея</a></p>
    </div>
  </main>
{:else if matchId && snapshot}
  <OverlayView {snapshot} connection={status} />
{:else if matchId}
  <main class="boot">
    <div class="card">
      <span class="mark">STK</span>
      <p>Подключение к overlay…</p>
      <div class="bar" aria-hidden="true"></div>
    </div>
  </main>
{:else}
  <main class="boot">
    <div class="card">
      <span class="mark">STK</span>
      <p>Загрузка…</p>
      <div class="bar" aria-hidden="true"></div>
    </div>
  </main>
{/if}

<style>
  .boot,
  .watch-deny {
    min-height: 100%;
    min-height: 100dvh;
    display: grid;
    place-items: center;
    padding: 2rem 1.25rem;
    background: var(--bg-base);
    color: var(--text);
    text-align: center;
    font-family: var(--font);
    font-weight: 500;
    position: relative;
  }
  .boot::before,
  .watch-deny::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(ellipse 80% 50% at 15% -5%, rgba(40, 44, 52, 0.35), transparent 55%),
      radial-gradient(ellipse 50% 40% at 95% 5%, rgba(50, 38, 18, 0.12), transparent 50%);
  }
  .card {
    position: relative;
    z-index: 1;
    max-width: 26rem;
    padding: 2rem 1.75rem 1.75rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    overflow: hidden;
    border-radius: var(--radius);
  }
  .card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
  }
  .mark {
    display: inline-grid;
    place-items: center;
    width: 2.75rem;
    height: 2.75rem;
    margin-bottom: 0.65rem;
    border-radius: var(--radius);
    background: var(--cta);
    color: var(--cta-text);
    font-weight: 700;
    font-size: 0.85rem;
  }
  .eyebrow {
    margin: 0 0 0.35rem;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    font-weight: 600;
  }
  .watch-deny h1 {
    margin: 0 0 0.55rem;
    font-family: var(--font-display);
    font-size: clamp(1.8rem, 4vw, 2.3rem);
    font-weight: 600;
    letter-spacing: -0.035em;
    text-transform: none;
  }
  .boot p,
  .watch-deny p {
    margin: 0;
    color: var(--text-muted);
    max-width: 22rem;
    margin-inline: auto;
    line-height: 1.45;
  }
  .watch-deny .tip {
    margin-top: 0.9rem;
    font-size: 0.9rem;
  }
  .bar {
    margin: 1.2rem auto 0;
    width: 7rem;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    background-size: 200% 100%;
    animation: slide 1.2s linear infinite;
  }
  @keyframes slide {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }
</style>
