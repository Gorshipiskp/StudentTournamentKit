<script lang="ts">
  import { onMount } from 'svelte';
  import { connectOverlayWs } from './connectOverlayWs';
  import { createMockWatchStream } from './mockStream';
  import { connectWatchSubscriber, type SubscriberStatus } from './signalingSubscriber';
  import {
    bannerLabel,
    fetchTurnCredentials,
    fetchWhepPlay,
    humanWatchError,
    mediaModeHint,
    mediaStatusLabel,
    redeemInvite,
    sceneLabel,
    type MediaMode,
    type RedeemResult,
  } from './watchAuth';
  import { connectWhepPlayer, type WhepStatus } from './whepClient';
  import {
    buildOverlayWsUrl,
    parseOverlaySnapshot,
    type OverlaySnapshot,
  } from './snapshot';

  let {
    inviteToken,
    mediaMode = 'whep',
  }: {
    inviteToken: string;
    mediaMode?: MediaMode;
  } = $props();

  let session = $state<RedeemResult | null>(null);
  let bootError = $state<string | null>(null);
  let loading = $state(true);
  let snapshot = $state<OverlaySnapshot | null>(null);
  let videoEl = $state<HTMLVideoElement | null>(null);
  let stageEl = $state<HTMLElement | null>(null);
  let mediaStatus = $state<SubscriberStatus | WhepStatus | 'mock'>('connecting');
  let mediaError = $state<string | null>(null);
  let waitingHint = $state(true);
  let muted = $state(true);
  let showChrome = $state(true);
  let chromeTimer: number | undefined;

  const techBanner = $derived(
    bannerLabel(snapshot?.data.judge.banner ?? null) ||
      (snapshot?.data.paused ? 'Техническая пауза' : null),
  );

  const modeHint = $derived(mediaModeHint(mediaMode));
  const liveOk = $derived(mediaStatus === 'live' || mediaStatus === 'mock');

  const brandStyle = $derived.by(() => {
    const b = snapshot?.data.branding;
    if (!b) return undefined;
    const primary = b.colors?.primary;
    const accent = b.colors?.accent;
    const parts = [
      primary ? `--brand-primary: ${primary}` : '',
      accent ? `--brand-accent: ${accent}` : '',
    ].filter(Boolean);
    return parts.length ? parts.join('; ') : undefined;
  });

  const waitingCopy = $derived(
    mediaMode === 'whep'
      ? {
          title: 'Ждём картинку эфира',
          sub: 'Режиссёр ещё не включил трансляцию. Экран обновится сам.',
        }
      : mediaMode === 'fake'
        ? {
            title: 'Ждём тестовый эфир',
            sub: 'Agent с тестовым каналом ещё не подключён. Это репетиция, не живой OBS.',
          }
        : {
            title: 'Ожидание эфира',
            sub: 'Подключаемся…',
          },
  );

  function pokeChrome() {
    showChrome = true;
    if (chromeTimer) window.clearTimeout(chromeTimer);
    if (liveOk && !techBanner) {
      chromeTimer = window.setTimeout(() => {
        showChrome = false;
      }, 3500);
    }
  }

  function attachStream(stream: MediaStream) {
    waitingHint = false;
    if (videoEl) {
      videoEl.srcObject = stream;
      videoEl.muted = muted;
      void videoEl.play().catch(() => {
        /* autoplay policies — user can unmute/play */
      });
    }
  }

  function toggleMute() {
    muted = !muted;
    if (videoEl) {
      videoEl.muted = muted;
      if (!muted) void videoEl.play().catch(() => undefined);
    }
    pokeChrome();
  }

  async function toggleFullscreen() {
    pokeChrome();
    const el = stageEl;
    if (!el) return;
    try {
      if (!document.fullscreenElement) {
        await el.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch {
      /* ignore */
    }
  }

  function retry() {
    window.location.reload();
  }

  function shortId(id: string): string {
    return id.length > 12 ? id.slice(0, 8) + '…' : id;
  }

  onMount(() => {
    let cancelled = false;
    const cleanups: Array<() => void> = [];
    pokeChrome();

    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (e.key === 'm' || e.key === 'M' || e.key === 'ь' || e.key === 'Ь') {
        e.preventDefault();
        toggleMute();
      }
      if (e.key === 'f' || e.key === 'F' || e.key === 'а' || e.key === 'А') {
        e.preventDefault();
        void toggleFullscreen();
      }
    };
    window.addEventListener('keydown', onKey);
    cleanups.push(() => window.removeEventListener('keydown', onKey));

    (async () => {
      try {
        const redeemed = await redeemInvite(inviteToken);
        if (cancelled) return;
        if (redeemed.role !== 'commentator') {
          bootError =
            'Эта ссылка не для комментатора. Попросите у организатора ссылку «смотреть».';
          loading = false;
          return;
        }
        if (!redeemed.caps.includes('commentator.watch')) {
          bootError = 'У приглашения нет права смотреть эфир. Нужна новая ссылка.';
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
            /* optional */
          },
        });
        cleanups.push(() => ovl.close());

        if (mediaMode === 'mock') {
          mediaStatus = 'mock';
          const handle = createMockWatchStream();
          attachStream(handle.stream);
          cleanups.push(() => handle.stop());
          return;
        }

        if (mediaMode === 'whep') {
          let creds;
          try {
            creds = await fetchWhepPlay(redeemed.match_id, redeemed.access_token);
          } catch (e) {
            mediaError = humanWatchError(
              e instanceof Error ? e.message : 'Не удалось получить доступ к эфиру',
            );
            mediaStatus = 'error';
            return;
          }
          if (cancelled) return;
          const player = connectWhepPlayer({
            credentials: creds,
            onStatus: (s) => {
              mediaStatus = s;
              if (s === 'waiting_publisher' || s === 'connecting') waitingHint = true;
              if (s === 'live') {
                waitingHint = false;
                mediaError = null;
                pokeChrome();
              }
            },
            onStream: attachStream,
            onError: (m) => {
              mediaError = humanWatchError(m);
            },
          });
          cleanups.push(() => player.close());
          return;
        }

        let turn = null;
        try {
          turn = await fetchTurnCredentials(redeemed.match_id, redeemed.access_token);
        } catch {
          /* STUN-only */
        }
        if (cancelled) return;

        const sub = connectWatchSubscriber({
          matchId: redeemed.match_id,
          accessToken: redeemed.access_token,
          turn,
          onStatus: (s) => {
            mediaStatus = s;
            if (s === 'waiting_offer') waitingHint = true;
            if (s === 'live') {
              waitingHint = false;
              pokeChrome();
            }
          },
          onStream: attachStream,
          onError: (m) => {
            mediaError = humanWatchError(m);
          },
        });
        cleanups.push(() => sub.close());
      } catch (e) {
        if (cancelled) return;
        bootError = humanWatchError(e instanceof Error ? e.message : 'Не удалось войти');
        loading = false;
      }
    })();

    return () => {
      cancelled = true;
      if (chromeTimer) window.clearTimeout(chromeTimer);
      for (const fn of cleanups) fn();
    };
  });
</script>

{#if loading}
  <main class="watch-app boot">
    <div class="boot-card">
      <span class="mark">STK</span>
      <p class="eyebrow">Студенческий эфир</p>
      <h1 class="display">Комментатор</h1>
      <p class="muted">Входим по приглашению…</p>
      <div class="bar" aria-hidden="true"></div>
    </div>
  </main>
{:else if bootError}
  <main class="watch-app boot deny">
    <div class="boot-card">
      <span class="mark warn">!</span>
      <h1 class="display">Доступ закрыт</h1>
      <p class="muted">{bootError}</p>
      <p class="tip muted">
        Ссылку выдаёт организатор из «Ссылки для команды». Не пересылайте её зрителям.
      </p>
    </div>
  </main>
{:else}
  <main
    class="watch-app"
    class:cinema={!showChrome && liveOk}
    style={brandStyle}
    onmousemove={pokeChrome}
    onpointerdown={pokeChrome}
  >
    <header class="chrome strip" class:hidden={!showChrome && liveOk}>
      <div class="brand">
        <span class="mark sm">STK</span>
        <div>
          <p class="eyebrow">Комментатор · низкая задержка</p>
          {#if snapshot?.data.tournament_name}
            <p class="tour">{snapshot.data.tournament_name}</p>
          {:else}
            <p class="tour muted">Матч {shortId(session?.match_id || '')}</p>
          {/if}
        </div>
      </div>

      {#if snapshot}
        <div class="scoreboard" aria-label="Счёт" aria-live="polite">
          <span class="team a">{snapshot.data.team_a.name}</span>
          <span class="nums">
            {#key snapshot.data.team_a.score}
              <span class="num a">{snapshot.data.team_a.score}</span>
            {/key}<span class="colon">:</span>{#key snapshot.data.team_b.score}
              <span class="num b">{snapshot.data.team_b.score}</span>
            {/key}
          </span>
          <span class="team b">{snapshot.data.team_b.name}</span>
        </div>
        <div class="meta-col">
          <span class="scene">{sceneLabel(snapshot.data.scene)}</span>
          {#if snapshot.data.map || snapshot.data.round}
            <span class="round-map">
              {#if snapshot.data.map}{snapshot.data.map}{/if}
              {#if snapshot.data.map && snapshot.data.round} · {/if}
              {#if snapshot.data.round}р. {snapshot.data.round}{/if}
            </span>
          {/if}
        </div>
      {/if}

      <div class="status-block">
        <span class="pill" class:live={liveOk} class:wait={!liveOk && mediaStatus !== 'error'}
          >{mediaStatusLabel(mediaStatus)}</span
        >
        {#if modeHint}
          <span class="mode-hint">{modeHint}</span>
        {/if}
      </div>
    </header>

    {#if techBanner}
      <div class="tech" role="status">
        <span class="tech-tag">Судья</span>
        <span>{techBanner}</span>
      </div>
    {/if}

    <div class="stage" bind:this={stageEl}>
      <video bind:this={videoEl} class="video" autoplay playsinline muted={muted}></video>

      {#if waitingHint && !liveOk && mediaStatus !== 'error'}
        <div class="wait">
          <div class="wait-card">
            <div class="pulse-row" aria-hidden="true">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
            <p class="display wait-title">{waitingCopy.title}</p>
            <p class="sub muted">{waitingCopy.sub}</p>
          </div>
        </div>
      {/if}

      <div class="controls chrome" class:hidden={!showChrome}>
        <button type="button" class="ctrl" onclick={toggleMute} title="Клавиша M">
          {muted ? 'Включить звук' : 'Выключить звук'}
          <kbd>M</kbd>
        </button>
        <button
          type="button"
          class="ctrl"
          onclick={() => void toggleFullscreen()}
          title="Клавиша F"
        >
          На весь экран
          <kbd>F</kbd>
        </button>
        {#if mediaError || mediaStatus === 'error'}
          <button type="button" class="ctrl primary" onclick={retry}>Повторить</button>
        {/if}
      </div>
    </div>

    {#if mediaError}
      <p class="err" role="alert">{mediaError}</p>
    {/if}

    <footer class="chrome foot" class:hidden={!showChrome && liveOk}>
      <p>До 2 вкладок комментатора на матч · звук и полный экран — клавиши M / F</p>
    </footer>
  </main>
{/if}

<style>
  .watch-app {
    --ink: var(--text);
    --muted: var(--text-muted);
    --faint: var(--text-dim);
    --accent-deep: var(--cta);
    min-height: 100%;
    min-height: 100dvh;
    background: var(--bg-base);
    color: var(--text);
    display: flex;
    flex-direction: column;
    font-family: var(--font);
    font-weight: 500;
    isolation: isolate;
    position: relative;
  }
  .watch-app::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: -1;
    background:
      radial-gradient(ellipse 80% 50% at 15% -5%, rgba(40, 44, 52, 0.35), transparent 55%),
      radial-gradient(ellipse 50% 40% at 95% 5%, rgba(50, 38, 18, 0.12), transparent 50%);
  }
  .display {
    font-family: var(--font-display);
    font-weight: 600;
    letter-spacing: -0.035em;
    text-transform: none;
  }
  .muted {
    color: var(--text-muted);
  }
  .boot {
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 2rem 1.25rem;
  }
  .boot-card {
    position: relative;
    max-width: 26rem;
    padding: 2rem 1.75rem 1.75rem;
    background: rgba(7, 16, 22, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
    overflow: hidden;
  }
  .boot-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent), var(--accent));
  }
  .mark {
    display: inline-grid;
    place-items: center;
    width: 2.75rem;
    height: 2.75rem;
    margin-bottom: 0.85rem;
    border-radius: 2px;
    background: var(--cta);
    color: var(--cta-text);
    font-weight: 800;
    font-size: 0.85rem;
  }
  .mark.sm {
    width: 2.2rem;
    height: 2.2rem;
    margin: 0;
    font-size: 0.7rem;
    flex-shrink: 0;
  }
  .mark.warn {
    background: #9f1239;
    font-size: 1.35rem;
  }
  .boot .eyebrow {
    margin: 0 0 0.35rem;
  }
  .boot h1 {
    margin: 0 0 0.55rem;
    font-size: clamp(1.8rem, 4vw, 2.3rem);
  }
  .boot p {
    margin: 0;
    max-width: 22rem;
    margin-inline: auto;
    line-height: 1.45;
  }
  .tip {
    margin-top: 1rem !important;
    font-size: 0.9rem;
  }
  .bar {
    margin: 1.35rem auto 0;
    width: 7.5rem;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent), transparent);
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
  .chrome.hidden {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.35s ease;
  }
  .chrome {
    transition: opacity 0.25s ease;
  }
  .cinema .stage {
    cursor: none;
  }
  .strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.1rem;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: linear-gradient(180deg, rgba(11, 20, 25, 0.96), rgba(7, 16, 22, 0.92));
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    min-width: 0;
  }
  .eyebrow {
    margin: 0;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--faint);
    font-weight: 700;
  }
  .tour {
    margin: 0.12rem 0 0;
    font-weight: 750;
    font-size: 0.98rem;
  }
  .scoreboard {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    padding: 0.35rem 0.75rem;
    background: rgba(0, 0, 0, 0.28);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .team {
    font-size: 0.92rem;
    font-weight: 750;
    max-width: 8.5rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .team.a {
    color: var(--brand-primary, var(--accent));
  }
  .team.b {
    color: var(--brand-accent, var(--accent));
  }
  .nums {
    font-family: var(--font-display);
    font-size: 1.45rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.02em;
    display: inline-flex;
    align-items: baseline;
  }
  .num {
    display: inline-block;
    animation: tick 0.4s cubic-bezier(0.22, 1, 0.36, 1);
  }
  .num.a {
    color: var(--brand-primary, var(--accent));
  }
  .num.b {
    color: var(--brand-accent, var(--accent));
  }
  @keyframes tick {
    from {
      transform: scale(1.12);
    }
    to {
      transform: scale(1);
    }
  }
  .colon {
    margin: 0 0.12rem;
    color: var(--faint);
  }
  .meta-col {
    display: flex;
    flex-direction: column;
    gap: 0.12rem;
    align-items: flex-start;
  }
  .scene {
    font-family: var(--font-display);
    font-size: 0.95rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink);
  }
  .round-map {
    font-size: 0.75rem;
    color: var(--muted);
  }
  .status-block {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.2rem;
  }
  .pill {
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.3rem 0.55rem;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.06);
    color: var(--muted);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .pill.live {
    background: color-mix(in srgb, var(--accent) 18%, transparent);
    border-color: color-mix(in srgb, var(--accent) 40%, transparent);
    color: var(--accent);
  }
  .pill.wait {
    background: color-mix(in srgb, var(--accent) 14%, transparent);
    border-color: color-mix(in srgb, var(--accent) 35%, transparent);
    color: var(--accent);
  }
  .mode-hint {
    font-size: 0.7rem;
    color: var(--faint);
  }
  .tech {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.55rem;
    background: color-mix(in srgb, var(--danger) 22%, #0b1419);
    color: #fecdd3;
    text-align: center;
    padding: 0.65rem 1rem;
    font-weight: 700;
    border-bottom: 1px solid rgba(255, 120, 120, 0.25);
  }
  .tech-tag {
    padding: 0.2rem 0.45rem;
    background: rgba(255, 255, 255, 0.1);
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .stage {
    position: relative;
    flex: 1;
    min-height: 52vh;
    background: #000;
  }
  .video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #000;
    min-height: 52vh;
  }
  .wait {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    background:
      radial-gradient(600px 320px at 50% 40%, rgba(212, 168, 75, 0.1), transparent 60%),
      rgba(7, 16, 22, 0.82);
    padding: 1.5rem;
  }
  .wait-card {
    position: relative;
    text-align: center;
    max-width: 24rem;
    padding: 1.6rem 1.4rem 1.4rem;
    background: rgba(7, 16, 22, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.4);
  }
  .wait-card::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent));
  }
  .pulse-row {
    display: flex;
    justify-content: center;
    gap: 0.4rem;
    margin-bottom: 1rem;
  }
  .dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 1.15s ease-in-out infinite;
  }
  .dot:nth-child(2) {
    animation-delay: 0.18s;
  }
  .dot:nth-child(3) {
    animation-delay: 0.36s;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.4;
      transform: scale(0.85);
    }
  }
  .wait-title {
    margin: 0 0 0.45rem;
    font-size: clamp(1.45rem, 3vw, 1.85rem);
  }
  .sub {
    margin: 0;
    font-size: 0.98rem;
    line-height: 1.45;
  }
  .controls {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    padding: 0.9rem 1rem calc(0.9rem + env(safe-area-inset-bottom));
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.78));
  }
  .ctrl {
    min-height: 2.65rem;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 0.9rem;
    border-radius: 2px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(11, 20, 25, 0.82);
    color: var(--ink);
    font: inherit;
    font-weight: 700;
    font-size: 0.9rem;
    cursor: pointer;
  }
  .ctrl:hover {
    border-color: color-mix(in srgb, var(--accent) 50%, white);
  }
  .ctrl.primary {
    background: var(--cta);
    border-color: var(--cta);
  }
  .ctrl kbd {
    display: inline-grid;
    place-items: center;
    min-width: 1.25rem;
    height: 1.25rem;
    padding: 0 0.25rem;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 2px;
    font-size: 0.68rem;
    font-weight: 800;
    color: var(--faint);
    font-family: inherit;
  }
  .err {
    margin: 0;
    padding: 0.75rem 1rem;
    background: color-mix(in srgb, var(--danger) 18%, #0b1419);
    color: #fecdd3;
    line-height: 1.4;
    border-top: 1px solid rgba(255, 120, 120, 0.25);
  }
  .foot {
    margin: 0;
    padding: 0.5rem 1rem 0.75rem;
    font-size: 0.75rem;
    color: var(--faint);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }
  .foot p {
    margin: 0;
  }

  @media (max-width: 720px) {
    .scoreboard {
      order: 3;
      width: 100%;
      justify-content: center;
    }
    .meta-col {
      order: 4;
      width: 100%;
      align-items: center;
      text-align: center;
    }
    .status-block {
      align-items: flex-start;
    }
  }
</style>
