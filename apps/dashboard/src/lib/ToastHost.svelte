<script lang="ts">
  import { onMount } from 'svelte';
  import { subscribeToasts, type ToastItem } from './toast';

  let items = $state<ToastItem[]>([]);

  onMount(() => subscribeToasts((next) => (items = next)));
</script>

{#if items.length}
  <div class="toasts" aria-live="polite" aria-relevant="additions">
    {#each items as t (t.id)}
      <div class="toast" class:ok={t.kind === 'ok'} class:err={t.kind === 'err'} role="status">
        {t.text}
      </div>
    {/each}
  </div>
{/if}

<style>
  .toasts {
    position: fixed;
    z-index: 80;
    right: 1rem;
    bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: min(22rem, calc(100vw - 2rem));
    pointer-events: none;
  }
  .toast {
    pointer-events: auto;
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    font-size: 0.92rem;
    line-height: 1.35;
    animation: in 0.2s ease;
  }
  .toast.ok {
    border-color: color-mix(in srgb, var(--ok) 45%, var(--border));
  }
  .toast.err {
    border-color: color-mix(in srgb, var(--danger) 45%, var(--border));
    color: var(--danger);
  }
  @keyframes in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
</style>
