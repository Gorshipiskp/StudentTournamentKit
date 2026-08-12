<script lang="ts">
  import type { OverlayData } from '../snapshot';
  import ScoreFlash from './ScoreFlash.svelte';

  let { data }: { data: OverlayData } = $props();

  const label = $derived(
    `${data.team_a.name} ${data.team_a.score} : ${data.team_b.score} ${data.team_b.name}, раунд ${data.round}`,
  );
</script>

<section class="scene ingame" aria-label={label}>
  <div class="board" class:paused-on={data.paused}>
    <div class="glow" aria-hidden="true"></div>
    <div class="sheen" aria-hidden="true"></div>
    <div class="edge top-rule" aria-hidden="true"></div>
    <div class="edge bot-rule" aria-hidden="true"></div>

    <div class="top">
      <div class="live" aria-hidden="true">
        <span class="live-dot"></span>
        LIVE
      </div>
      {#if data.tournament_name}
        <p class="tour">{data.tournament_name}</p>
      {/if}
      {#if data.paused}
        <span class="paused">Пауза</span>
      {/if}
    </div>

    <div class="row">
      <div class="side a">
        <span class="slot">CT</span>
        <div class="team">
          <span class="name">{data.team_a.name}</span>
          <span class="under" aria-hidden="true"></span>
        </div>
        <span class="score"><ScoreFlash value={data.team_a.score} tone="a" /></span>
      </div>

      <div class="mid">
        <span class="vs" aria-hidden="true">VS</span>
        <span class="round">Раунд {data.round}</span>
        {#if data.map}<span class="map">{data.map}</span>{/if}
      </div>

      <div class="side b right">
        <span class="score"><ScoreFlash value={data.team_b.score} tone="b" /></span>
        <div class="team">
          <span class="name">{data.team_b.name}</span>
          <span class="under" aria-hidden="true"></span>
        </div>
        <span class="slot">T</span>
      </div>
    </div>
  </div>
</section>

<style>
  .ingame {
    --side-a: #8ec4f0;
    --side-a-soft: rgba(142, 196, 240, 0.45);
    --side-b: #f0a86a;
    --side-b-soft: rgba(240, 168, 106, 0.45);
    --board-ink: #fff8eb;
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    padding: 0;
    margin: 0;
    display: block;
    width: 100%;
  }

  .board {
    position: relative;
    width: 100%;
    min-width: 100%;
    max-width: none;
    margin: 0;
    padding: 0.75rem 1.5rem 0.9rem;
    border: none;
    border-radius: 0;
    background:
      linear-gradient(180deg, #0b1218 0%, #070c10 100%),
      radial-gradient(ellipse 80% 120% at 50% 0%, rgba(212, 168, 75, 0.14), transparent 60%);
    background-color: #070c10;
    box-shadow:
      0 14px 36px rgba(0, 0, 0, 0.65),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    overflow: hidden;
    animation: board-in 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .glow {
    position: absolute;
    inset: -40% -10% auto;
    height: 90%;
    background: radial-gradient(ellipse at 50% 0%, rgba(212, 168, 75, 0.18), transparent 65%);
    pointer-events: none;
    animation: glow-breathe 4.5s ease-in-out infinite;
  }

  .sheen {
    position: absolute;
    top: 0;
    left: -30%;
    width: 40%;
    height: 100%;
    background: linear-gradient(
      100deg,
      transparent 0%,
      rgba(255, 255, 255, 0.07) 45%,
      transparent 70%
    );
    transform: skewX(-18deg);
    pointer-events: none;
    animation: board-sheen 5.5s 0.6s ease-in-out infinite;
  }

  .edge {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    pointer-events: none;
  }

  .top-rule {
    top: 0;
    background: linear-gradient(90deg, transparent, var(--brand-primary, #d4a84b), transparent);
    transform: scaleX(0.35);
    animation: rule-expand 0.7s 0.1s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .bot-rule {
    bottom: 0;
    height: 3px;
    background: linear-gradient(
      90deg,
      var(--side-a) 0%,
      var(--brand-primary, #d4a84b) 50%,
      var(--side-b) 100%
    );
    box-shadow: 0 0 16px rgba(212, 168, 75, 0.35);
    transform: scaleX(0.2);
    animation: rule-expand 0.75s 0.18s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .top {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    min-height: 1.25rem;
    margin-bottom: 0.35rem;
  }

  .live {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.14rem 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(0, 0, 0, 0.35);
    font-family: var(--font-display);
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.2em;
  }

  .live-dot {
    width: 0.38rem;
    height: 0.38rem;
    border-radius: 50%;
    background: var(--danger, #d48484);
    box-shadow: 0 0 10px rgba(212, 132, 132, 0.7);
    animation: ov-pulse 1.1s ease-in-out infinite;
  }

  .tour {
    margin: 0;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--brand-primary, var(--accent));
    text-shadow: 0 0 18px color-mix(in srgb, var(--brand-primary, #d4a84b) 35%, transparent);
    max-width: 42vw;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .paused {
    padding: 0.14rem 0.5rem;
    background: color-mix(in srgb, var(--danger, #d48484) 22%, transparent);
    border: 1px solid color-mix(in srgb, var(--danger, #d48484) 45%, transparent);
    color: #fecaca;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .row {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1rem;
  }

  .side {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    min-width: 0;
  }

  .side.right {
    justify-content: flex-end;
  }

  .slot {
    flex-shrink: 0;
    min-width: 1.7rem;
    height: 1.35rem;
    padding: 0 0.35rem;
    display: inline-grid;
    place-items: center;
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    border: 1px solid rgba(255, 255, 255, 0.14);
    background: rgba(0, 0, 0, 0.28);
  }

  .side.a .slot {
    color: var(--side-a);
    border-color: color-mix(in srgb, var(--side-a) 45%, transparent);
    box-shadow: 0 0 12px var(--side-a-soft);
  }

  .side.b .slot {
    color: var(--side-b);
    border-color: color-mix(in srgb, var(--side-b) 45%, transparent);
    box-shadow: 0 0 12px var(--side-b-soft);
  }

  .team {
    display: flex;
    flex-direction: column;
    gap: 0.22rem;
    min-width: 0;
  }

  .side.right .team {
    align-items: flex-end;
  }

  .name {
    font-family: var(--font-display);
    font-size: clamp(0.95rem, 1.7vw, 1.25rem);
    font-weight: 750;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--board-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 22vw;
  }

  .under {
    display: block;
    width: 100%;
    max-width: 9rem;
    height: 2px;
    transform: scaleX(0.25);
    transform-origin: left center;
    animation: under-draw 0.65s 0.25s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .side.right .under {
    transform-origin: right center;
  }

  .side.a .under {
    background: linear-gradient(90deg, var(--side-a), transparent);
  }

  .side.b .under {
    background: linear-gradient(270deg, var(--side-b), transparent);
  }

  .score {
    font-family: var(--font-display);
    font-size: clamp(2.35rem, 4vw, 3.1rem);
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    line-height: 0.9;
    letter-spacing: 0.02em;
  }

  .side.a .score {
    color: var(--side-a);
    text-shadow: 0 0 22px var(--side-a-soft);
  }

  .side.b .score {
    color: var(--side-b);
    text-shadow: 0 0 22px var(--side-b-soft);
  }

  .mid {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.12rem;
    min-width: 7rem;
    padding: 0 0.4rem;
  }

  .vs {
    font-family: var(--font-display);
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 0.28em;
    color: rgba(255, 248, 235, 0.35);
  }

  .round {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--brand-primary, var(--accent));
    text-shadow: 0 0 14px color-mix(in srgb, var(--brand-primary, #d4a84b) 40%, transparent);
  }

  .map {
    color: rgba(255, 248, 235, 0.45);
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.02em;
  }

  .paused-on {
    box-shadow:
      0 18px 48px rgba(0, 0, 0, 0.45),
      0 0 0 1px color-mix(in srgb, var(--danger, #d48484) 35%, transparent);
  }

  @keyframes board-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes rule-expand {
    from {
      transform: scaleX(0.15);
      opacity: 0;
    }
    to {
      transform: scaleX(1);
      opacity: 1;
    }
  }

  @keyframes under-draw {
    from {
      transform: scaleX(0.15);
      opacity: 0;
    }
    to {
      transform: scaleX(1);
      opacity: 1;
    }
  }

  @keyframes board-sheen {
    0%,
    70%,
    100% {
      transform: translateX(0) skewX(-18deg);
      opacity: 0;
    }
    78% {
      opacity: 1;
    }
    92% {
      transform: translateX(280%) skewX(-18deg);
      opacity: 0;
    }
  }

  @keyframes glow-breathe {
    0%,
    100% {
      opacity: 0.7;
    }
    50% {
      opacity: 1;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .board,
    .top-rule,
    .bot-rule,
    .under,
    .sheen,
    .glow,
    .live-dot {
      animation: none !important;
    }

    .top-rule,
    .bot-rule,
    .under {
      transform: scaleX(1);
      opacity: 1;
    }
  }
</style>
