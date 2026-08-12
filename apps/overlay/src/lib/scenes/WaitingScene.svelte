<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import BrandMark from './BrandMark.svelte';

  let { data }: { data: OverlayData } = $props();

  const live = $derived(data.match_status === 'live');
</script>

<section class="scene waiting" aria-label={live ? 'Эфир: сцена ожидания' : 'Ожидание'}>
  <div class="frame ov-panel ov-enter">
    <div class="accent" aria-hidden="true"></div>
    <div class="head">
      <BrandMark {data} />
    </div>
    {#if live}
      <h1>Матч уже идёт</h1>
      <p class="hint">
        Счёт {data.team_a.score}:{data.team_b.score} — на эфире всё ещё «Ожидание».
        В пульте режиссёра выбери сцену <strong>Игра</strong>.
      </p>
    {:else}
      <h1>Матч скоро начнётся</h1>
      <p class="hint">Готовим эфир · команды на подходе</p>
    {/if}
    <div class="pulse-row" aria-hidden="true">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</section>

<style>
  .waiting {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: 4vh 4vw;
  }

  .frame {
    min-width: min(68vw, 820px);
    padding: 2.2rem 3rem 2.2rem;
    text-align: center;
  }

  .accent {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(
      180deg,
      var(--brand-primary, var(--accent)),
      var(--brand-accent, var(--campus))
    );
    z-index: 2;
  }

  .head {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .head :global(.brand-mark) {
    justify-content: center;
    text-align: center;
  }

  .head :global(.text) {
    text-align: left;
  }

  h1 {
    margin: 0.35rem 0 0;
    font-family: var(--font-display);
    font-size: clamp(2.4rem, 5.2vw, 4rem);
    font-weight: 800;
    letter-spacing: 0.02em;
    line-height: 0.95;
    text-transform: uppercase;
  }

  .hint {
    margin: 0.9rem 0 0;
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.45;
    max-width: 36rem;
    margin-inline: auto;
  }

  .hint strong {
    color: var(--ink);
  }

  .pulse-row {
    display: flex;
    justify-content: center;
    gap: 0.45rem;
    margin-top: 1.5rem;
  }

  .dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 50%;
    background: var(--brand-primary, var(--accent));
    animation: ov-pulse 1.2s ease-in-out infinite;
  }

  .dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .dot:nth-child(3) {
    animation-delay: 0.4s;
  }
</style>
