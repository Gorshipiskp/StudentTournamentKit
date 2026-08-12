<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import BrandMark from './BrandMark.svelte';
  import ScoreFlash from './ScoreFlash.svelte';

  let { data }: { data: OverlayData } = $props();

  const winner = $derived(
    data.team_a.score === data.team_b.score
      ? null
      : data.team_a.score > data.team_b.score
        ? data.team_a
        : data.team_b,
  );
</script>

<section class="scene winner" aria-label="Победитель">
  <div class="frame ov-panel ov-enter-late">
    <div class="glow" aria-hidden="true"></div>
    <div class="head">
      <BrandMark {data} />
    </div>
    <p class="label">Победитель матча</p>
    {#if winner}
      <h1>{winner.name}</h1>
    {:else}
      <h1>Ничья</h1>
      <p class="duo">{data.team_a.name} · {data.team_b.name}</p>
    {/if}
    <p class="score" aria-label="Итоговый счёт">
      <ScoreFlash value={data.team_a.score} tone="a" />
      <span class="sep">:</span>
      <ScoreFlash value={data.team_b.score} tone="b" />
    </p>
    <div class="ribbon" aria-hidden="true"></div>
  </div>
</section>

<style>
  .winner {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 4vh 4vw;
  }

  .frame {
    min-width: min(70vw, 880px);
    padding: 2.4rem 3rem 2.4rem;
    text-align: center;
    border: 1px solid color-mix(in srgb, var(--brand-primary, var(--accent)) 45%, transparent);
  }

  .glow {
    position: absolute;
    inset: -20% -10% auto;
    height: 55%;
    background: radial-gradient(
      ellipse at center,
      color-mix(in srgb, var(--brand-primary, var(--accent)) 28%, transparent),
      transparent 70%
    );
    pointer-events: none;
    z-index: 0;
  }

  .head {
    display: flex;
    justify-content: center;
    margin-bottom: 0.75rem;
  }

  .label {
    margin: 0 0 0.75rem;
    font-size: 0.88rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--brand-accent, var(--campus));
  }

  h1 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(2.6rem, 6vw, 4.2rem);
    font-weight: 800;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    line-height: 0.95;
  }

  .duo {
    margin: 0.65rem 0 0;
    color: var(--muted);
    font-size: 1.05rem;
  }

  .score {
    margin: 1.2rem 0 0;
    font-family: var(--font-display);
    font-size: clamp(1.6rem, 3.2vw, 2.3rem);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .sep {
    margin: 0 0.25rem;
    color: var(--muted);
  }

  .ribbon {
    margin: 1.35rem auto 0;
    width: 5.5rem;
    height: 4px;
    background: linear-gradient(
      90deg,
      var(--brand-primary, var(--accent)),
      var(--brand-accent, var(--campus))
    );
  }
</style>
