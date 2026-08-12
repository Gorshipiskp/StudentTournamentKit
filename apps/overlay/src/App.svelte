<script lang="ts">
  import type { OverlaySnapshot } from './lib/snapshot';
  import {
    buildOverlayWsUrl,
    resolveMatchId,
  } from './lib/snapshot';
  import { connectOverlayWs } from './lib/connectOverlayWs';
  import OverlayView from './lib/OverlayView.svelte';
  import WatchPage from './lib/WatchPage.svelte';
  import {
    isMockWatch,
    isWatchPath,
    resolveWatchInviteToken,
  } from './lib/watchAuth';
  import { onMount } from 'svelte';

  let mode = $state<'overlay' | 'watch' | 'boot'>('boot');
  let matchId = $state<string | null>(null);
  let watchToken = $state<string | null>(null);
  let watchMock = $state(false);
  let snapshot = $state<OverlaySnapshot | null>(null);
  let status = $state<'connecting' | 'open' | 'closed' | 'error' | 'idle'>('idle');
  let error = $state<string | null>(null);

  onMount(() => {
    const path = window.location.pathname;
    const search = window.location.search;

    if (isWatchPath(path)) {
      const token = resolveWatchInviteToken(path, search);
      mode = 'watch';
      watchToken = token;
      watchMock = isMockWatch(search);
      if (!token) {
        error = 'Откройте /watch?token=<invite> или /watch/<invite>';
      }
      return;
    }

    mode = 'overlay';
    const id = resolveMatchId(path, search);
    matchId = id;
    if (!id) {
      error = 'Укажите матч в URL: /overlay/{matchId}';
      return;
    }

    const url = buildOverlayWsUrl(id);
    const session = connectOverlayWs(url, {
      onSnapshot: (snap) => {
        snapshot = snap;
        error = null;
      },
      onStatus: (s) => {
        status = s;
      },
    });

    return () => session.close();
  });
</script>

{#if mode === 'watch'}
  {#if error && !watchToken}
    <main class="boot deny">
      <h1>Комментатор</h1>
      <p>{error}</p>
    </main>
  {:else if watchToken}
    <WatchPage inviteToken={watchToken} mock={watchMock} />
  {/if}
{:else if error && !snapshot}
  <main class="boot">
    <p>{error}</p>
  </main>
{:else if matchId && snapshot}
  <OverlayView {snapshot} connection={status} />
{:else if matchId}
  <main class="boot"><p>Подключение к overlay…</p></main>
{:else}
  <main class="boot"><p>Загрузка…</p></main>
{/if}

<style>
  .boot {
    min-height: 100%;
    display: grid;
    place-items: center;
    padding: 2rem;
    background: #0c1118;
    color: #eef2f6;
    text-align: center;
  }
  .deny h1 {
    margin: 0 0 0.75rem;
  }
  .deny p {
    color: var(--muted);
  }
</style>
