<script lang="ts">
  import type { Snippet } from 'svelte';
  import ToastHost from './ToastHost.svelte';

  let {
    title,
    subtitle = null,
    tournamentName = null,
    tournamentId = null,
    current = null,
    showLogout = false,
    loading = false,
    onlogout,
    children,
    footer = undefined,
  }: {
    title: string;
    subtitle?: string | null;
    tournamentName?: string | null;
    tournamentId?: string | null;
    current?: 'list' | 'teams' | 'bracket' | 'branding' | null;
    showLogout?: boolean;
    loading?: boolean;
    onlogout?: () => void;
    children: Snippet;
    footer?: Snippet;
  } = $props();

  const base = $derived(
    tournamentId ? `/admin/tournaments/${encodeURIComponent(tournamentId)}` : null,
  );

  const railSteps = $derived(
    base
      ? [
          { id: 'list' as const, label: 'Турниры', href: '/admin' },
          { id: 'teams' as const, label: 'Команды', href: base },
          { id: 'bracket' as const, label: 'Сетка', href: `${base}/bracket` },
          { id: 'branding' as const, label: 'Оформление', href: `${base}/branding` },
        ]
      : [{ id: 'list' as const, label: 'Турниры', href: '/admin' }],
  );
</script>

<div class="admin-app" class:has-footer={!!footer}>
  <div class="layout">
    <aside class="rail" aria-label="Навигация организатора">
      <a class="brand-block" href="/admin">
        <span class="mark">STK</span>
        <span class="brand-name display">Организатор</span>
      </a>
      {#if tournamentName}
        <p class="tour-name">{tournamentName}</p>
      {/if}

      <nav class="rail-nav" aria-label="Разделы">
        {#each railSteps as step (step.id)}
          {#if current === step.id}
            <span class="rail-link cur" aria-current="page">{step.label}</span>
          {:else}
            <a class="rail-link" href={step.href}>{step.label}</a>
          {/if}
        {/each}
      </nav>

      {#if showLogout && onlogout}
        <button type="button" class="btn btn-ghost logout" onclick={onlogout}>Выйти</button>
      {/if}
    </aside>

    <div class="main-col">
      <header class="top">
        <div>
          <h1 class="display">{title}</h1>
          {#if subtitle}
            <p class="sub muted">{subtitle}</p>
          {/if}
        </div>
        {#if showLogout && onlogout}
          <button type="button" class="btn btn-ghost logout-mobile" onclick={onlogout}
            >Выйти</button
          >
        {/if}
      </header>

      {#if loading}
        <div class="loading-banner" role="status">Загружаем…</div>
      {/if}

      <div class="content" class:dim={loading}>
        {@render children()}
      </div>
    </div>
  </div>

  {#if footer}
    <div class="sticky-footer">
      {@render footer()}
    </div>
  {/if}

  <ToastHost />
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: 1fr;
    min-height: 100vh;
  }
  .admin-app.has-footer .main-col {
    padding-bottom: 5.5rem;
  }
  .rail {
    display: none;
  }
  .main-col {
    padding: 1.25rem 1.15rem 3rem;
    max-width: 72rem;
    width: 100%;
    margin: 0 auto;
  }
  .top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }
  h1 {
    margin: 0;
    font-size: clamp(1.45rem, 2.8vw, 1.85rem);
  }
  .sub {
    margin: 0.3rem 0 0;
    font-size: 0.95rem;
  }
  .logout-mobile {
    flex-shrink: 0;
  }
  .loading-banner {
    margin-bottom: 0.85rem;
    padding: 0.55rem 0.85rem;
    border-radius: var(--radius-sm);
    background: var(--accent-muted);
    color: var(--accent);
    font-weight: 600;
    font-size: 0.9rem;
    border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  }
  .content.dim {
    opacity: 0.55;
    pointer-events: none;
  }
  .sticky-footer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 40;
    padding: 0.75rem 1rem calc(0.75rem + env(safe-area-inset-bottom));
    background: rgba(8, 9, 11, 0.92);
    border-top: 1px solid var(--border);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  @media (min-width: 900px) {
    .layout {
      grid-template-columns: 15.5rem minmax(0, 1fr);
    }
    .rail {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 1.5rem 1.15rem;
      border-right: 1px solid var(--border);
      background: rgba(8, 9, 11, 0.72);
      position: sticky;
      top: 0;
      align-self: start;
      min-height: 100vh;
    }
    .brand-block {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      text-decoration: none;
      color: inherit;
    }
    .mark {
      display: inline-grid;
      place-items: center;
      width: 2.4rem;
      height: 2.4rem;
      border-radius: var(--radius);
      background: var(--cta);
      color: var(--cta-text);
      font-weight: 700;
      font-size: 0.85rem;
    }
    .brand-name {
      font-size: 1.05rem;
      line-height: 1.25;
    }
    .tour-name {
      margin: 0.35rem 0 0;
      font-weight: 600;
      font-size: 0.9rem;
      line-height: 1.3;
      color: var(--text-muted);
    }
    .rail-nav {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      margin-top: 0.75rem;
    }
    .rail-link {
      display: block;
      padding: 0.45rem 0.65rem;
      border-radius: var(--radius-sm);
      text-decoration: none;
      color: var(--text-dim);
      font-weight: 500;
      font-size: 0.88rem;
      position: relative;
    }
    .rail-link:hover {
      color: var(--text-muted);
      background: var(--bg-hover);
    }
    .rail-link.cur {
      color: var(--text);
      background: transparent;
    }
    .rail-link.cur::before {
      content: '';
      position: absolute;
      left: 0;
      top: 20%;
      bottom: 20%;
      width: 2px;
      border-radius: 1px;
      background: var(--accent);
    }
    .logout {
      margin-top: auto;
      width: 100%;
    }
    .logout-mobile {
      display: none;
    }
    .main-col {
      padding: 2rem 2rem 4rem;
    }
    .sticky-footer {
      left: 15.5rem;
    }
  }
</style>
