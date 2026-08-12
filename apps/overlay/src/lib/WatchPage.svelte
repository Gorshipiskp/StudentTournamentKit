<script lang="ts">
  import { onMount } from 'svelte';
  import { connectOverlayWs } from './connectOverlayWs';
  import { createMockWatchStream } from './mockStream';
  import { connectWatchSubscriber, type SubscriberStatus } from './signalingSubscriber';
  import {
    bannerLabel,
    fetchTurnCredentials,
    redeemInvite,
    type RedeemResult,
  } from './watchAuth';
  import {
    buildOverlayWsUrl,
    parseOverlaySnapshot,
    type OverlaySnapshot,
  } from './snapshot';

  let {
    inviteToken,
    mock = false,
  }: {
    inviteToken: string;
    mock?: boolean;
  } = $props();

  let session = $state<RedeemResult | null>(null);
  let bootError = $state<string | null>(null);
  let loading = $state(true);
  let snapshot = $state<OverlaySnapshot | null>(null);
  let videoEl = $state<HTMLVideoElement | null>(null);
  let mediaStatus = $state<SubscriberStatus | 'mock'>('connecting');
  let mediaError = $state<string | null>(null);
  let waitingHint = $state(true);

  const techBanner = $derived(
    bannerLabel(snapshot?.data.judge.banner ?? null) ||
      (snapshot?.data.paused ? 'Техническая пауза' : null),
  );

  function attachStream(stream: MediaStream) {
    waitingHint = false;
    if (videoEl) {
      videoEl.srcObject = stream;
      void videoEl.play().catch(() => {
        /* autoplay policies */
      });
    }
  }

  onMount(() => {
    let cancelled = false;
    const cleanups: Array<() => void> = [];

    (async () => {
      try {
        const redeemed = await redeemInvite(inviteToken);
        if (cancelled) return;
        if (redeemed.role !== 'commentator') {
          bootError = 'Эта ссылка не для комментатора.';
          loading = false;
          return;
        }
        if (!redeemed.caps.includes('commentator.watch')) {
          bootError = 'Нет права просмотра эфира.';
          loading = false;
          return;
        }
        session = redeemed;
        loading = false;

        const ovl = connectOverlayWs(buildOverlayWsUrl(redeemed.match_id), {
          onSnapshot: (raw) => {
            try {
              snapshot = parseOverlaySnapshot(raw);
            } catch {
              /* ignore bad frames */
            }
          },
          onStatus: () => {
            /* overlay link status optional */
          },
        });
        cleanups.push(() => ovl.close());

        if (mock) {
          mediaStatus = 'mock';
          const handle = createMockWatchStream();
          attachStream(handle.stream);
          cleanups.push(() => handle.stop());
          return;
        }

        let turn = null;
        try {
          turn = await fetchTurnCredentials(redeemed.match_id, redeemed.access_token);
        } catch {
          /* STUN-only fallback */
        }
        if (cancelled) return;

        const sub = connectWatchSubscriber({
          matchId: redeemed.match_id,
          accessToken: redeemed.access_token,
          turn,
          onStatus: (s) => {
            mediaStatus = s;
            if (s === 'waiting_offer') waitingHint = true;
          },
          onStream: attachStream,
          onError: (m) => {
            mediaError = m;
          },
        });
        cleanups.push(() => sub.close());
      } catch (e) {
        if (cancelled) return;
        bootError = e instanceof Error ? e.message : 'Не удалось войти';
        loading = false;
      }
    })();

    return () => {
      cancelled = true;
      for (const fn of cleanups) fn();
    };
  });
</script>

{#if loading}
  <main class="watch boot"><p>Вход по приглашению…</p></main>
{:else if bootError}
  <main class="watch boot deny">
    <h1>Доступ закрыт</h1>
    <p>{bootError}</p>
  </main>
{:else}
  <main class="watch">
    <header class="strip">
      <div class="left">
        <span class="label">Комментатор</span>
        <span class="match">{session?.match_id}</span>
      </div>
      {#if snapshot}
        <div class="score">
          {snapshot.data.team_a.name}
          {snapshot.data.team_a.score}:{snapshot.data.team_b.score}
          {snapshot.data.team_b.name}
        </div>
      {/if}
      <div class="right">
        {#if mediaStatus === 'mock'}
          mock
        {:else if mediaStatus === 'live'}
          эфир
        {:else if mediaStatus === 'waiting_offer' || mediaStatus === 'connecting'}
          ожидание
        {:else}
          {mediaStatus}
        {/if}
      </div>
    </header>

    {#if techBanner}
      <div class="tech" role="status">{techBanner}</div>
    {/if}

    <div class="stage">
      <video bind:this={videoEl} class="video" autoplay playsinline muted></video>
      {#if waitingHint && mediaStatus !== 'live' && mediaStatus !== 'mock'}
        <div class="wait">
          <p>Ожидание эфира</p>
          <p class="sub">Режиссёр ещё не подключился (Agent publisher).</p>
        </div>
      {/if}
    </div>

    {#if mediaError}
      <p class="err" role="alert">{mediaError}</p>
    {/if}
    <p class="limit">До 2 одновременных вкладок /watch на матч.</p>
  </main>
{/if}

<style>
  .watch {
    min-height: 100%;
    min-height: 100dvh;
    background: #0c1118;
    color: #eef2f6;
    display: flex;
    flex-direction: column;
  }
  .boot {
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem;
  }
  .deny h1 {
    margin: 0 0 0.75rem;
    font-size: 1.5rem;
  }
  .deny p {
    color: var(--muted);
  }
  .strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: #151c26;
    border-bottom: 1px solid #243040;
  }
  .label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.7rem;
    color: var(--muted);
    margin-right: 0.5rem;
  }
  .match {
    font-size: 0.85rem;
    word-break: break-all;
  }
  .score {
    font-weight: 700;
    font-size: 1.05rem;
  }
  .right {
    color: var(--accent);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .tech {
    background: color-mix(in srgb, var(--danger) 35%, #151c26);
    color: #ffd7d7;
    text-align: center;
    padding: 0.65rem 1rem;
    font-weight: 600;
  }
  .stage {
    position: relative;
    flex: 1;
    min-height: 50vh;
    background: #05070b;
  }
  .video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #000;
    min-height: 50vh;
  }
  .wait {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(5, 7, 11, 0.72);
    text-align: center;
    padding: 1.5rem;
  }
  .wait p {
    margin: 0.25rem 0;
    font-size: 1.25rem;
  }
  .wait .sub {
    color: var(--muted);
    font-size: 0.95rem;
  }
  .err {
    margin: 0;
    padding: 0.6rem 1rem;
    background: color-mix(in srgb, var(--danger) 25%, transparent);
    color: #ffb4b4;
  }
  .limit {
    margin: 0;
    padding: 0.45rem 1rem 0.75rem;
    font-size: 0.75rem;
    color: var(--muted);
  }
</style>
