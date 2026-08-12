<script lang="ts">
  import { onDestroy } from 'svelte';
  import type { OverlayFx } from '../snapshot';

  let { fx }: { fx: OverlayFx | null } = $props();

  let visible = $state(false);
  let shown = $state<OverlayFx | null>(null);
  let remaining = $state<number | null>(null);
  let hideTimer: number | undefined;
  let tickTimer: number | undefined;

  const SPARKS = Array.from({ length: 18 }, (_, i) => i);

  function clearTimers() {
    if (hideTimer) window.clearTimeout(hideTimer);
    if (tickTimer) window.clearInterval(tickTimer);
    hideTimer = undefined;
    tickTimer = undefined;
  }

  function applyFx(next: OverlayFx | null) {
    clearTimers();
    remaining = null;
    if (!next) {
      visible = false;
      shown = null;
      return;
    }

    const ttl = Math.max(800, next.ttl_ms || 4000);
    shown = next;
    visible = true;

    if (next.kind === 'bomb_planted' && next.timer_sec) {
      const plantedAt = Date.parse(next.at);
      const base = Number.isFinite(plantedAt) ? plantedAt : Date.now();
      const update = () => {
        const elapsed = (Date.now() - base) / 1000;
        remaining = Math.max(0, Math.ceil(next.timer_sec! - elapsed));
      };
      update();
      tickTimer = window.setInterval(update, 200);
    }

    hideTimer = window.setTimeout(() => {
      visible = false;
      remaining = null;
    }, ttl);
  }

  let lastSeq: number | null | undefined = undefined;

  $effect(() => {
    const next = fx;
    const seq = next?.seq ?? null;
    if (seq === lastSeq) return;
    lastSeq = seq;
    applyFx(next);
  });

  onDestroy(clearTimers);

  const kindClass = $derived(shown?.kind ? `kind-${shown.kind}` : '');
  const sideClass = $derived(
    shown?.side === 'team_a' ? 'side-a' : shown?.side === 'team_b' ? 'side-b' : '',
  );
  const sideLabel = $derived(
    shown?.side === 'team_a'
      ? 'Контр-террористы'
      : shown?.side === 'team_b'
        ? 'Террористы'
        : 'Раунд завершён',
  );
</script>

{#if visible && shown}
  {#key shown.seq}
    <div
      class="fx {kindClass} {sideClass}"
      role="status"
      aria-live="polite"
      data-seq={shown.seq}
    >
      {#if shown.kind === 'round_win'}
        <div class="shade" aria-hidden="true"></div>
        <div class="shutter top" aria-hidden="true"></div>
        <div class="shutter bottom" aria-hidden="true"></div>
        <div class="shock" aria-hidden="true"><i></i><i></i><i></i></div>
        <div class="streak" aria-hidden="true"></div>
        <div class="sparks" aria-hidden="true">
          {#each SPARKS as s (s)}
            <i style="--i: {s}"></i>
          {/each}
        </div>
        <div class="headline">
          <p class="eyebrow">
            <span>Раунд{shown.round ? ` ${shown.round}` : ''}</span>
          </p>
          <p class="win-title">
            <span class="glow">{shown.label}</span>
            <span class="solid" aria-hidden="true">{shown.label}</span>
          </p>
          <div class="rule" aria-hidden="true"></div>
          <p class="win-meta">{sideLabel}</p>
        </div>
      {:else}
        <div class="fx-card">
          {#if shown.kind === 'bomb_planted'}
            <div class="ring" aria-hidden="true"></div>
            <div class="ring delay" aria-hidden="true"></div>
            <p class="eyebrow">C4</p>
            <p class="title">{shown.label}</p>
            {#if remaining != null}
              <p class="timer tabular">{remaining}<span>с</span></p>
            {/if}
            {#if shown.site != null}
              <p class="meta">Сайт {shown.site}</p>
            {/if}
          {:else if shown.kind === 'bomb_defusing'}
            <div class="pulse-bar" aria-hidden="true"></div>
            <p class="eyebrow">Дефьюз</p>
            <p class="title">{shown.has_kit ? 'С китом' : 'Без кита'}</p>
          {:else if shown.kind === 'bomb_defused'}
            <div class="ok-flash" aria-hidden="true"></div>
            <p class="eyebrow">CT</p>
            <p class="title">{shown.label}</p>
          {:else if shown.kind === 'bomb_exploded'}
            <div class="flash" aria-hidden="true"></div>
            <p class="eyebrow">T</p>
            <p class="title">{shown.label}</p>
          {:else}
            <p class="title">{shown.label}</p>
          {/if}
        </div>
      {/if}
    </div>
  {/key}
{/if}

<style>
  .fx {
    position: absolute;
    inset: 0;
    z-index: 8;
    pointer-events: none;
    display: grid;
    place-items: center;
    overflow: hidden;
  }

  .fx:not(.kind-round_win) {
    place-items: start center;
    padding-top: 14vh;
    animation: card-stage-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  /* —— Round win: cinematic, not a card —— */
  .kind-round_win {
    --fx: #d4a84b;
    --fx-soft: rgba(212, 168, 75, 0.55);
  }

  .side-a.kind-round_win {
    --fx: #8ec4f0;
    --fx-soft: rgba(142, 196, 240, 0.55);
  }

  .side-b.kind-round_win {
    --fx: #f0a86a;
    --fx-soft: rgba(240, 168, 106, 0.55);
  }

  .shade {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 70% 55% at 50% 48%, transparent 20%, rgba(0, 0, 0, 0.55) 100%),
      linear-gradient(180deg, rgba(0, 0, 0, 0.35), transparent 28%, transparent 72%, rgba(0, 0, 0, 0.4));
    animation: shade-in 0.55s ease-out both;
  }

  .shutter {
    position: absolute;
    left: 0;
    right: 0;
    height: 11vh;
    background: linear-gradient(
      180deg,
      rgba(4, 8, 12, 0.92),
      rgba(4, 8, 12, 0.55) 55%,
      transparent
    );
    transform-origin: center;
  }

  .shutter.top {
    top: 0;
    animation: shutter-top 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .shutter.bottom {
    bottom: 0;
    background: linear-gradient(
      0deg,
      rgba(4, 8, 12, 0.92),
      rgba(4, 8, 12, 0.55) 55%,
      transparent
    );
    animation: shutter-bottom 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .shock {
    position: absolute;
    left: 50%;
    top: 48%;
    width: min(70vw, 720px);
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
  }

  .shock i {
    position: absolute;
    inset: 0;
    border: 2px solid var(--fx-soft);
    border-radius: 50%;
    opacity: 0;
    animation: shockwave 1.15s cubic-bezier(0.12, 0.7, 0.2, 1) both;
  }

  .shock i:nth-child(2) {
    animation-delay: 0.12s;
  }

  .shock i:nth-child(3) {
    animation-delay: 0.24s;
  }

  .streak {
    position: absolute;
    left: -20%;
    top: 46%;
    width: 140%;
    height: 3px;
    background: linear-gradient(90deg, transparent 0%, var(--fx) 35%, #fff 50%, var(--fx) 65%, transparent 100%);
    filter: blur(0.4px);
    box-shadow: 0 0 28px var(--fx-soft);
    transform: translateX(-30%) skewX(-18deg);
    opacity: 0;
    animation: streak-slash 0.75s 0.08s cubic-bezier(0.2, 0.9, 0.2, 1) both;
  }

  .sparks {
    position: absolute;
    inset: 0;
  }

  .sparks i {
    --ang: calc(var(--i) * 20deg);
    --dist: calc(18vmin + (var(--i) % 5) * 4vmin);
    position: absolute;
    left: 50%;
    top: 48%;
    width: 5px;
    height: 5px;
    margin: -2px;
    border-radius: 50%;
    background: var(--fx);
    box-shadow: 0 0 10px var(--fx-soft);
    opacity: 0;
    animation: spark-fly 1.05s calc(0.05s + var(--i) * 0.018s) cubic-bezier(0.15, 0.85, 0.25, 1) both;
  }

  .sparks i:nth-child(odd) {
    width: 3px;
    height: 10px;
    border-radius: 2px;
  }

  .headline {
    position: relative;
    z-index: 2;
    text-align: center;
    padding: 0 4vw;
    max-width: 92vw;
  }

  .eyebrow {
    margin: 0 auto 0.85rem;
    overflow: hidden;
    font-size: clamp(0.7rem, 1.4vw, 0.9rem);
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: color-mix(in srgb, var(--fx) 85%, white);
  }

  .eyebrow span {
    display: inline-block;
    animation: rise-mask 0.55s 0.18s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .win-title {
    position: relative;
    margin: 0;
    font-family: var(--font-display, inherit);
    font-size: clamp(2.6rem, 8.5vw, 5.4rem);
    font-weight: 800;
    letter-spacing: 0.06em;
    line-height: 0.95;
    text-transform: uppercase;
  }

  .win-title .glow,
  .win-title .solid {
    display: block;
  }

  .win-title .glow {
    color: transparent;
    background: linear-gradient(100deg, transparent 20%, #fff 45%, var(--fx) 55%, transparent 80%);
    background-size: 220% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    filter: blur(0.4px);
    opacity: 0.95;
    animation:
      title-slam 0.7s 0.12s cubic-bezier(0.16, 1, 0.3, 1) both,
      sheen 1.4s 0.35s ease-out both;
  }

  .win-title .solid {
    position: absolute;
    inset: 0;
    color: var(--fx);
    text-shadow:
      0 0 28px var(--fx-soft),
      0 8px 30px rgba(0, 0, 0, 0.65);
    animation: title-slam 0.7s 0.12s cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .rule {
    width: min(42vw, 280px);
    height: 2px;
    margin: 1.1rem auto 0;
    background: linear-gradient(90deg, transparent, var(--fx), transparent);
    transform: scaleX(0);
    transform-origin: center;
    animation: rule-draw 0.55s 0.38s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .win-meta {
    margin: 0.85rem 0 0;
    font-size: clamp(0.8rem, 1.6vw, 1.05rem);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(255, 248, 235, 0.82);
    animation: rise-mask 0.55s 0.48s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  /* —— Bomb / misc cards —— */
  .fx-card {
    position: relative;
    min-width: min(42vw, 320px);
    padding: 1rem 1.35rem 1.05rem;
    text-align: center;
    background: rgba(8, 9, 11, 0.78);
    border: 1px solid var(--border-strong, rgba(255, 248, 235, 0.12));
    border-radius: var(--radius, 4px);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
    overflow: hidden;
    animation: card-pop 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .title {
    margin: 0.35rem 0 0;
    font-family: var(--font-display, inherit);
    font-size: clamp(1.35rem, 2.8vw, 1.85rem);
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .fx:not(.kind-round_win) .eyebrow {
    margin: 0;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--accent, #d4a84b);
  }

  .timer {
    margin: 0.55rem 0 0;
    font-family: var(--mono, ui-monospace, monospace);
    font-size: clamp(2rem, 4vw, 2.8rem);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--accent, #d4a84b);
    line-height: 1;
  }

  .timer span {
    margin-left: 0.2rem;
    font-size: 0.55em;
    color: var(--text-muted, #9a948a);
  }

  .meta {
    margin: 0.4rem 0 0;
    font-size: 0.85rem;
    color: var(--text-muted, #9a948a);
  }

  .ring {
    position: absolute;
    inset: -40%;
    border: 2px solid color-mix(in srgb, var(--accent, #d4a84b) 35%, transparent);
    border-radius: 50%;
    animation: ring-pulse 1.4s ease-out infinite;
  }

  .ring.delay {
    animation-delay: 0.45s;
  }

  .pulse-bar {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent, #d4a84b), transparent);
    background-size: 200% 100%;
    animation: bar-slide 1s linear infinite;
  }

  .flash,
  .ok-flash {
    position: absolute;
    inset: 0;
    animation: flash-fade 0.8s ease-out both;
  }

  .flash {
    background: radial-gradient(circle at 50% 30%, rgba(212, 132, 132, 0.4), transparent 65%);
  }

  .ok-flash {
    background: radial-gradient(circle at 50% 30%, rgba(107, 184, 148, 0.35), transparent 65%);
  }

  .kind-bomb_exploded .title {
    color: var(--danger, #d48484);
  }

  .kind-bomb_defused .title {
    color: var(--ok, #6bb894);
  }

  @keyframes shade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes shutter-top {
    from {
      transform: translateY(-110%);
    }
    to {
      transform: translateY(0);
    }
  }

  @keyframes shutter-bottom {
    from {
      transform: translateY(110%);
    }
    to {
      transform: translateY(0);
    }
  }

  @keyframes shockwave {
    0% {
      transform: scale(0.15);
      opacity: 0.85;
    }
    70% {
      opacity: 0.25;
    }
    100% {
      transform: scale(1.15);
      opacity: 0;
    }
  }

  @keyframes streak-slash {
    0% {
      opacity: 0;
      transform: translateX(-55%) skewX(-18deg);
    }
    25% {
      opacity: 1;
    }
    100% {
      opacity: 0;
      transform: translateX(35%) skewX(-18deg);
    }
  }

  @keyframes spark-fly {
    0% {
      opacity: 0;
      transform: rotate(var(--ang)) translateY(0) scale(0.4);
    }
    18% {
      opacity: 1;
    }
    100% {
      opacity: 0;
      transform: rotate(var(--ang)) translateY(calc(var(--dist) * -1)) scale(1);
    }
  }

  @keyframes title-slam {
    0% {
      opacity: 0;
      transform: scale(1.35) translateY(18px);
      filter: blur(8px);
      letter-spacing: 0.28em;
    }
    55% {
      filter: blur(0);
    }
    100% {
      opacity: 1;
      transform: scale(1) translateY(0);
      filter: blur(0);
      letter-spacing: 0.06em;
    }
  }

  @keyframes sheen {
    from {
      background-position: 120% 0;
    }
    to {
      background-position: -40% 0;
    }
  }

  @keyframes rise-mask {
    from {
      opacity: 0;
      transform: translateY(120%);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes rule-draw {
    from {
      transform: scaleX(0);
      opacity: 0;
    }
    to {
      transform: scaleX(1);
      opacity: 1;
    }
  }

  @keyframes card-stage-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes card-pop {
    from {
      opacity: 0;
      transform: translateY(14px) scale(0.94);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes ring-pulse {
    from {
      transform: scale(0.55);
      opacity: 0.7;
    }
    to {
      transform: scale(1.05);
      opacity: 0;
    }
  }

  @keyframes bar-slide {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }

  @keyframes flash-fade {
    from {
      opacity: 1;
    }
    to {
      opacity: 0.3;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .fx,
    .fx *,
    .sparks i,
    .shock i,
    .streak,
    .shutter,
    .shade,
    .win-title .glow,
    .win-title .solid,
    .eyebrow span,
    .win-meta,
    .rule {
      animation: none !important;
    }

    .win-title .solid {
      opacity: 1;
      color: var(--fx);
    }
  }
</style>
