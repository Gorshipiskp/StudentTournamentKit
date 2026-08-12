<script lang="ts">
  let {
    open = false,
    title = 'Подтвердите',
    body = '',
    confirmLabel = 'Подтвердить',
    cancelLabel = 'Назад',
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
    class="box surface"
    onsubmit={(e) => {
      e.preventDefault();
      onconfirm();
    }}
  >
    <h2 class="display">{title}</h2>
    {#if body}
      <p class="muted">{body}</p>
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
    max-width: calc(100vw - 1.5rem);
  }
  .dlg::backdrop {
    background: rgb(26 33 30 / 0.5);
  }
  .box {
    width: min(22rem, 100%);
    margin: auto;
    padding: 1.25rem 1.2rem;
  }
  h2 {
    margin: 0 0 0.5rem;
    font-size: 1.3rem;
  }
  p {
    margin: 0 0 1.1rem;
    line-height: 1.45;
  }
  .actions {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
</style>
