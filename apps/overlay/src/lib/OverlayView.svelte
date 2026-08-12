<script lang="ts">
  import type { OverlaySnapshot } from './snapshot';
  import { emptyOverlaySnapshot } from './snapshot';

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
</script>

<div
  class="stage scene-{scene}"
  class:has-brand={Boolean(branding)}
  data-version={snap.version}
  style={styleVars || undefined}
>
  {#if branding?.logo_url}
    <img class="brand-logo" src={branding.logo_url} alt="" />
  {/if}
  {#if scene === 'waiting'}
    <section class="panel center">
      <p class="eyebrow">Ожидание</p>
      <h1>Матч скоро начнётся</h1>
    </section>
  {:else if scene === 'intro'}
    <section class="panel center">
      <p class="eyebrow">Интро</p>
      <h1>{data.team_a.name} <span class="vs">vs</span> {data.team_b.name}</h1>
      {#if data.map}<p class="meta">{data.map}</p>{/if}
    </section>
  {:else if scene === 'teams'}
    <section class="panel teams">
      <div class="team">
        <h2>{data.team_a.name}</h2>
      </div>
      <div class="team right">
        <h2>{data.team_b.name}</h2>
      </div>
    </section>
  {:else if scene === 'break'}
    <section class="panel center">
      <p class="eyebrow">Перерыв</p>
      <h1>{data.team_a.score} : {data.team_b.score}</h1>
    </section>
  {:else if scene === 'winner'}
    <section class="panel center">
      <p class="eyebrow">Победитель</p>
      <h1>
        {data.team_a.score >= data.team_b.score ? data.team_a.name : data.team_b.name}
      </h1>
      <p class="meta">{data.team_a.score} : {data.team_b.score}</p>
    </section>
  {:else}
    <!-- ingame + default -->
    <section class="scoreboard" aria-label="Счёт матча">
      <div class="side">
        <span class="name">{data.team_a.name}</span>
        <span class="score">{data.team_a.score}</span>
      </div>
      <div class="mid">
        <span class="round">Раунд {data.round}</span>
        {#if data.map}<span class="map">{data.map}</span>{/if}
        {#if data.paused}<span class="paused">Пауза</span>{/if}
      </div>
      <div class="side right">
        <span class="score">{data.team_b.score}</span>
        <span class="name">{data.team_b.name}</span>
      </div>
    </section>
  {/if}

  {#if banner}
    <div class="judge-banner" role="status">{banner}</div>
  {/if}

  <!-- F4: watermark always rendered -->
  <div class="watermark" aria-hidden="true">{wm}</div>

  {#if connection !== 'open'}
    <div class="conn" title={connection}>●</div>
  {/if}
</div>

<style>
  .stage {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 2.5vh 2.5vw;
  }

  .stage.has-brand {
    --panel-accent: var(--brand-primary, var(--accent, #3d9a86));
  }

  .stage.has-brand::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: var(--brand-bg, none);
    background-size: cover;
    background-position: center;
    opacity: 0.22;
    pointer-events: none;
    z-index: 0;
  }

  .brand-logo {
    position: absolute;
    top: 2.5vh;
    left: 2.5vw;
    max-height: 7vh;
    max-width: 18vw;
    object-fit: contain;
    z-index: 3;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.45));
  }

  .panel {
    position: absolute;
    left: 50%;
    top: 42%;
    transform: translate(-50%, -50%);
    min-width: min(72vw, 920px);
    padding: 2rem 2.5rem;
    border-radius: 4px;
    background: var(--panel);
    backdrop-filter: blur(6px);
    text-align: center;
  }

  .panel.teams {
    display: flex;
    justify-content: space-between;
    gap: 2rem;
    text-align: left;
  }

  .team.right {
    text-align: right;
  }

  .eyebrow {
    margin: 0 0 0.4rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-size: 0.75rem;
    color: var(--brand-primary, var(--accent));
  }

  .panel,
  .scoreboard,
  .judge-banner,
  .watermark,
  .brand-logo {
    z-index: 2;
  }

  h1 {
    margin: 0;
    font-size: clamp(1.8rem, 4vw, 3rem);
    font-weight: 700;
  }

  h2 {
    margin: 0;
    font-size: clamp(1.4rem, 3vw, 2.2rem);
  }

  .vs {
    opacity: 0.55;
    font-weight: 500;
  }

  .meta {
    margin: 0.75rem 0 0;
    color: var(--muted);
  }

  .scoreboard {
    position: absolute;
    left: 50%;
    top: 3.5vh;
    transform: translateX(-50%);
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1.25rem;
    min-width: min(70vw, 860px);
    padding: 0.85rem 1.4rem;
    border-radius: 4px;
    background: var(--panel);
    backdrop-filter: blur(6px);
  }

  .side {
    display: flex;
    align-items: baseline;
    gap: 0.85rem;
  }

  .side.right {
    justify-content: flex-end;
  }

  .name {
    font-size: 1.15rem;
    font-weight: 600;
  }

  .score {
    font-size: 2rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
  }

  .mid {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.15rem;
    color: var(--muted);
    font-size: 0.85rem;
  }

  .paused {
    color: var(--danger);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .judge-banner {
    position: absolute;
    left: 50%;
    bottom: 12vh;
    transform: translateX(-50%);
    padding: 0.55rem 1.2rem;
    border-radius: 4px;
    background: rgba(180, 40, 40, 0.78);
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .watermark {
    position: absolute;
    right: 1.4vw;
    bottom: 1.6vh;
    font-size: 0.72rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: rgba(242, 244, 247, 0.22);
    pointer-events: none;
    user-select: none;
  }

  .conn {
    position: absolute;
    left: 1.2vw;
    bottom: 1.4vh;
    color: var(--danger);
    font-size: 0.7rem;
    opacity: 0.85;
  }
</style>
