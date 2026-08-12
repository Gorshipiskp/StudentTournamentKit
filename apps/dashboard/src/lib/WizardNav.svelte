<script lang="ts">
  /** Wizard steps for organizer admin (RU action labels). */
  let {
    tournamentId = null,
    current = 'list',
  }: {
    tournamentId?: string | null;
    current: 'list' | 'teams' | 'bracket' | 'branding';
  } = $props();

  const base = $derived(
    tournamentId ? `/admin/tournaments/${encodeURIComponent(tournamentId)}` : null,
  );

  const steps = $derived(
    base
      ? [
          { id: 'list', label: '1. Турниры', href: '/admin' },
          { id: 'teams', label: '2. Команды', href: base },
          { id: 'bracket', label: '3. Сетка и старт', href: `${base}/bracket` },
          { id: 'branding', label: '4. Брендинг', href: `${base}/branding` },
        ]
      : [{ id: 'list', label: '1. Турниры', href: '/admin' }],
  );
</script>

<nav class="wizard" aria-label="Шаги настройки турнира">
  {#each steps as step, i (step.id)}
    {#if i > 0}<span class="sep" aria-hidden="true">→</span>{/if}
    {#if step.id === current}
      <span class="cur" aria-current="step">{step.label}</span>
    {:else}
      <a href={step.href}>{step.label}</a>
    {/if}
  {/each}
</nav>

<style>
  .wizard {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.5rem;
    align-items: center;
    margin: 0 0 1.25rem;
    padding: 0.65rem 0.8rem;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.88rem;
  }
  .wizard a {
    color: var(--muted);
    text-decoration: none;
  }
  .wizard a:hover {
    color: var(--accent);
  }
  .cur {
    color: var(--ink);
    font-weight: 650;
  }
  .sep {
    color: var(--border);
  }
</style>
