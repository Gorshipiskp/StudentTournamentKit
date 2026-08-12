<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import BrandMark from './BrandMark.svelte';

  let { data }: { data: OverlayData } = $props();
</script>

<section class="scene intro" aria-label="Интро">
  <div class="frame ov-panel ov-enter-late">
    <div class="head">
      <BrandMark {data} />
    </div>
    <div class="matchup">
      <div class="team-block left">
        <span class="side">Команда A</span>
        <h1 class="team">{data.team_a.name}</h1>
      </div>
      <div class="vs-wrap" aria-hidden="true">
        <span class="vs">VS</span>
      </div>
      <div class="team-block right">
        <span class="side">Команда B</span>
        <h1 class="team">{data.team_b.name}</h1>
      </div>
    </div>
    {#if data.map}
      <p class="ov-meta map">Карта · {data.map}</p>
    {/if}
  </div>
</section>

<style>
  .intro {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 4vh 4vw;
  }

  .frame {
    min-width: min(82vw, 1040px);
    padding: 2rem 2.6rem 2.1rem;
    text-align: center;
    border-top: 3px solid var(--brand-primary, var(--accent));
  }

  .head {
    display: flex;
    justify-content: center;
    margin-bottom: 1.1rem;
  }

  .matchup {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1.1rem;
  }

  .team-block {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-width: 0;
  }

  .team-block.left {
    text-align: left;
    align-items: flex-start;
    border-left: 3px solid var(--brand-primary, var(--accent));
    padding-left: 0.85rem;
  }

  .team-block.right {
    text-align: right;
    align-items: flex-end;
    border-right: 3px solid var(--brand-accent, var(--campus));
    padding-right: 0.85rem;
  }

  .side {
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--faint);
    font-weight: 700;
  }

  .team {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(2rem, 4.4vw, 3.4rem);
    font-weight: 800;
    line-height: 1;
    text-transform: uppercase;
    letter-spacing: 0.01em;
    word-break: break-word;
  }

  .vs-wrap {
    display: grid;
    place-items: center;
    width: 3.4rem;
    height: 3.4rem;
    border-radius: 50%;
    border: 1px solid var(--edge);
    background: rgba(0, 0, 0, 0.25);
  }

  .vs {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 1.15rem;
    letter-spacing: 0.08em;
    color: var(--brand-accent, var(--campus));
  }

  .map {
    margin-top: 1.25rem;
    padding-top: 0.9rem;
    border-top: 1px solid var(--edge-soft);
  }
</style>
