<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import BrandMark from './BrandMark.svelte';

  let { data }: { data: OverlayData } = $props();
</script>

<section class="scene teams" aria-label="Команды">
  <div class="shell ov-enter">
    <BrandMark {data} />
    <h1 class="title">Кто играет</h1>
    <div class="row">
      <article class="card ov-panel a">
        <p class="side">Команда A</p>
        <h2>{data.team_a.name}</h2>
        <div class="stripe" aria-hidden="true"></div>
      </article>
      <div class="divider" aria-hidden="true">
        <span>VS</span>
      </div>
      <article class="card ov-panel b">
        <p class="side">Команда B</p>
        <h2>{data.team_b.name}</h2>
        <div class="stripe" aria-hidden="true"></div>
      </article>
    </div>
    {#if data.map}
      <p class="ov-meta">Карта · {data.map}</p>
    {/if}
  </div>
</section>

<style>
  .teams {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 6vh 5vw;
  }

  .shell {
    width: min(90vw, 1120px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.85rem;
  }

  .title {
    margin: 0.15rem 0 0.55rem;
    font-family: var(--font-display);
    font-size: clamp(1.6rem, 3vw, 2.2rem);
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .row {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: stretch;
    gap: 1rem;
  }

  .card {
    padding: 1.7rem 1.9rem 1.5rem;
    min-height: 20vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .card.a {
    text-align: left;
  }

  .card.b {
    text-align: right;
  }

  .stripe {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 3px;
    z-index: 2;
  }

  .card.a .stripe {
    background: var(--brand-primary, var(--accent));
  }

  .card.b .stripe {
    background: var(--brand-accent, var(--campus));
  }

  .side {
    margin: 0 0 0.45rem;
    color: var(--faint);
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 700;
  }

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(1.9rem, 3.6vw, 3rem);
    font-weight: 800;
    line-height: 1.05;
    text-transform: uppercase;
    letter-spacing: 0.01em;
  }

  .divider {
    display: grid;
    place-items: center;
    padding: 0 0.35rem;
    font-family: var(--font-display);
    font-weight: 800;
    letter-spacing: 0.12em;
    color: var(--campus);
    font-size: 1.2rem;
  }
</style>
