<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import BrandMark from './BrandMark.svelte';
  import ScoreFlash from './ScoreFlash.svelte';

  let { data }: { data: OverlayData } = $props();
</script>

<section class="scene break" aria-label="Перерыв">
  <div class="frame ov-panel ov-enter">
    <div class="head">
      <BrandMark {data} compact />
    </div>
    <p class="label">Перерыв между раундами</p>
    <div class="scoreline">
      <span class="team">{data.team_a.name}</span>
      <span class="score"
        ><ScoreFlash value={data.team_a.score} tone="a" /><i>:</i><ScoreFlash
          value={data.team_b.score}
          tone="b"
        /></span
      >
      <span class="team right">{data.team_b.name}</span>
    </div>
    {#if data.map}
      <p class="ov-meta">{data.map}{#if data.round} · раунд {data.round}{/if}</p>
    {:else if data.round}
      <p class="ov-meta">Раунд {data.round}</p>
    {/if}
  </div>
</section>

<style>
  .break {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 4vh 4vw;
  }

  .frame {
    min-width: min(76vw, 960px);
    padding: 2rem 2.6rem 2.1rem;
    text-align: center;
    border-top: 3px solid var(--brand-accent, var(--campus));
  }

  .head {
    display: flex;
    justify-content: center;
    margin-bottom: 0.65rem;
  }

  .label {
    margin: 0 0 1.05rem;
    font-family: var(--font-display);
    font-size: clamp(1.3rem, 2.4vw, 1.7rem);
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .scoreline {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1rem;
  }

  .team {
    font-size: clamp(1.15rem, 2.5vw, 1.7rem);
    font-weight: 700;
    text-align: left;
    min-width: 0;
    word-break: break-word;
  }

  .team.right {
    text-align: right;
  }

  .score {
    display: inline-flex;
    align-items: baseline;
    gap: 0.35rem;
    font-family: var(--font-display);
    font-size: clamp(2.6rem, 5.4vw, 3.8rem);
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    line-height: 1;
  }

  .score i {
    font-style: normal;
    color: var(--faint);
    font-weight: 700;
  }

  .ov-meta {
    margin-top: 1.1rem;
  }
</style>
