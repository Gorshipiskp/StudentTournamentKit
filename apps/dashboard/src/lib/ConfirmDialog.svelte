<script lang="ts">
  import { onMount } from 'svelte';

  let {
    open = false,
    title = 'Подтвердите',
    body = '',
    confirmLabel = 'Удалить',
    cancelLabel = 'Отмена',
    danger = true,
    onconfirm,
    oncancel,
  }: {
    open?: boolean;
    title?: string;
    body?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    danger?: boolean;
    onconfirm: () => void;
    oncancel: () => void;
  } = $props();

  let dialogEl = $state<HTMLDialogElement | null>(null);

  $effect(() => {
    const el = dialogEl;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  });

  onMount(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) oncancel();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });
</script>

<dialog
  bind:this={dialogEl}
  class="dlg"
  onclose={oncancel}
  onclick={(e) => {
    if (e.target === dialogEl) oncancel();
  }}
>
  <form
    method="dialog"
    class="box"
    onsubmit={(e) => {
      e.preventDefault();
      onconfirm();
    }}
  >
    <h2 class="display">{title}</h2>
    {#if body}
      <p>{body}</p>
    {/if}
    <div class="actions">
      <button type="button" class="btn btn-ghost" onclick={oncancel}>{cancelLabel}</button>
      <button type="submit" class="btn" class:btn-danger={danger} class:btn-primary={!danger}>
        {confirmLabel}
      </button>
    </div>
  </form>
</dialog>

<style>
  .dlg {
    border: none;
    padding: 0;
    background: transparent;
    max-width: calc(100vw - 2rem);
  }
  .dlg::backdrop {
    background: rgb(28 36 33 / 0.45);
  }
  .box {
    width: min(24rem, 100%);
    margin: auto;
    padding: 1.25rem 1.35rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
  }
  h2 {
    margin: 0 0 0.5rem;
    font-size: 1.25rem;
  }
  p {
    margin: 0 0 1.1rem;
    color: var(--muted);
    line-height: 1.45;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
</style>
