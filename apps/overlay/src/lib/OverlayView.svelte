<script lang="ts">
  import type { OverlaySnapshot } from './snapshot';
  import { emptyOverlaySnapshot } from './snapshot';
  import WaitingScene from './scenes/WaitingScene.svelte';
  import IntroScene from './scenes/IntroScene.svelte';
  import TeamsScene from './scenes/TeamsScene.svelte';
  import IngameScene from './scenes/IngameScene.svelte';
  import BreakScene from './scenes/BreakScene.svelte';
  import WinnerScene from './scenes/WinnerScene.svelte';
  import EventFx from './scenes/EventFx.svelte';

  let {
    snapshot = null,
    connection = 'open',
  }: {
    snapshot?: OverlaySnapshot | null;
    connection?: string;
  } = $props();

  const snap = $derived(snapshot ?? emptyOverlaySnapshot());
  const data = $derived(snap.data);
  const scene = $derived(data.scene || 'waiting');
  const banner = $derived(data.judge.banner);
  const wm = $derived(data.watermark.text || 'STP');
  const branding = $derived(data.branding);
  const primary = $derived(branding?.colors?.primary || '');
  const accent = $derived(branding?.colors?.accent || '');
  const styleVars = $derived(
    [
      primary ? `--brand-primary: ${primary}` : '',
      accent ? `--brand-accent: ${accent}` : '',
      branding?.bg_url ? `--brand-bg: url(${branding.bg_url})` : '',
    ]
      .filter(Boolean)
      .join('; '),
  );

  const scoreLive = $derived(
    `${data.team_a.name} ${data.team_a.score} : ${data.team_b.score} ${data.team_b.name}`,
  );

  const floatLogo = $derived(Boolean(branding?.logo_url) && scene === 'ingame');
  const showDebugChip = $derived(
    typeof location !== 'undefined' &&
      new URLSearchParams(location.search).has('debug'),
  );
  const liveFx = $derived(data.fx ?? null);
</script>

<div
  class="stage scene-{scene}"
  class:has-brand={Boolean(branding)}
  class:has-logo={Boolean(branding?.logo_url)}
  data-version={snap.version}
  style={styleVars || undefined}
>
  {#if floatLogo}
    <img class="brand-logo" src={branding!.logo_url!} alt="" />
  {/if}

  {#key scene}
    {#if scene === 'waiting'}
      <WaitingScene {data} />
    {:else if scene === 'intro'}
      <IntroScene {data} />
    {:else if scene === 'teams'}
      <TeamsScene {data} />
    {:else if scene === 'ingame'}
      <IngameScene {data} />
    {:else if scene === 'break'}
      <BreakScene {data} />
    {:else if scene === 'winner'}
      <WinnerScene {data} />
    {:else}
      <IngameScene {data} />
    {/if}
  {/key}

  <EventFx fx={liveFx} />

  {#if showDebugChip}
    <div class="scene-chip" aria-hidden="true">{scene} · v{snap.version}</div>
  {/if}

  <div class="sr-live" aria-live="polite">{scoreLive}</div>

  {#if banner}
    <div class="judge-banner" role="status" aria-live="assertive">
      <span class="judge-tag">Судья</span>
      <span>{banner}</span>
    </div>
  {/if}

  <div class="watermark" aria-hidden="true">{wm}</div>

  {#if connection !== 'open'}
    <div class="conn" role="status" title={connection} aria-label="Нет связи с overlay">●</div>
  {/if}
</div>

<style>
  .stage {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 0;
  }

  .stage.has-brand {
    --panel-accent: var(--brand-primary, var(--accent));
  }

  .stage.has-brand::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: var(--brand-bg, none);
    background-size: cover;
    background-position: center;
    opacity: 0.2;
    pointer-events: none;
    z-index: 0;
  }

  .stage.has-brand::after {
    content: '';
    position: absolute;
    inset: 0;
    background:
      radial-gradient(
        70% 55% at 50% 0%,
        color-mix(in srgb, var(--brand-primary, var(--accent)) 16%, transparent),
        transparent 65%
      ),
      linear-gradient(
        180deg,
        transparent 70%,
        color-mix(in srgb, var(--brand-accent, var(--campus)) 8%, transparent)
      );
    pointer-events: none;
    z-index: 0;
  }

  .brand-logo {
    position: absolute;
    top: 2vh;
    left: 2vw;
    max-height: 6.5vh;
    max-width: 14vw;
    object-fit: contain;
    z-index: 3;
    padding: 0.35rem 0.45rem;
    background: rgba(7, 16, 22, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.1);
    filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.5));
  }

  .judge-banner,
  .watermark,
  .brand-logo {
    z-index: 2;
  }

  .judge-banner {
    position: absolute;
    left: 50%;
    bottom: 11vh;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 0.65rem;
    max-width: min(80vw, 640px);
    padding: 0.55rem 1rem 0.55rem 0.55rem;
    border-radius: 2px;
    background: rgba(120, 18, 28, 0.88);
    border: 1px solid rgba(255, 120, 120, 0.35);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    font-weight: 700;
    letter-spacing: 0.02em;
    animation: ov-rise 0.35s ease-out both;
  }

  .judge-tag {
    flex-shrink: 0;
    padding: 0.28rem 0.55rem;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.12);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .watermark {
    position: absolute;
    right: 1.5vw;
    bottom: 1.5vh;
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: rgba(242, 247, 245, 0.2);
    pointer-events: none;
    user-select: none;
  }

  .conn {
    position: absolute;
    left: 1.2vw;
    bottom: 1.4vh;
    color: var(--danger);
    font-size: 0.7rem;
    opacity: 0.9;
    z-index: 2;
    animation: ov-pulse 1.4s ease-in-out infinite;
  }

  .scene-chip {
    position: absolute;
    left: 1.2vw;
    top: 1.2vh;
    z-index: 4;
    padding: 0.22rem 0.5rem;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(242, 247, 245, 0.45);
    background: rgba(0, 0, 0, 0.28);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    pointer-events: none;
    user-select: none;
  }

  .stage.has-logo.scene-ingame .scene-chip {
    left: calc(2vw + 14vw + 0.6rem);
  }

  .sr-live {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
</style>
