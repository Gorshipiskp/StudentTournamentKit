<script lang="ts">
  import type { OverlayData } from '../snapshot';

  let {
    data,
    compact = false,
  }: {
    data: OverlayData;
    compact?: boolean;
  } = $props();

  const name = $derived(data.tournament_name || 'Студенческий турнир');
  const logo = $derived(data.branding?.logo_url || null);
</script>

<div class="brand-mark" class:compact aria-hidden="true">
  {#if logo}
    <img class="logo" src={logo} alt="" />
  {/if}
  <div class="text">
    <p class="tag">Турнир</p>
    <p class="name">{name}</p>
  </div>
</div>

<style>
  .brand-mark {
    display: inline-flex;
    align-items: center;
    gap: 0.7rem;
    text-align: left;
    max-width: min(70vw, 420px);
  }
  .brand-mark.compact {
    gap: 0.5rem;
  }
  .logo {
    width: 2.6rem;
    height: 2.6rem;
    object-fit: contain;
    flex-shrink: 0;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.45));
  }
  .compact .logo {
    width: 1.9rem;
    height: 1.9rem;
  }
  .tag {
    margin: 0;
    font-size: 0.62rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--brand-primary, var(--accent));
  }
  .name {
    margin: 0.1rem 0 0;
    font-family: var(--font-display);
    font-size: clamp(1rem, 2vw, 1.25rem);
    font-weight: 800;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    line-height: 1.05;
    color: var(--ink);
  }
  .compact .name {
    font-size: 0.95rem;
  }
</style>
