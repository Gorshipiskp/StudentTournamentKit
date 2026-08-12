<script lang="ts">
  /** Progress steps for organizer admin. */
  let {
    tournamentId = null,
    current = 'list',
  }: {
    tournamentId?: string | null;
    current: 'list' | 'teams' | 'bracket' | 'branding';
    tournamentName?: string | null;
  } = $props();

  const base = $derived(
    tournamentId ? `/admin/tournaments/${encodeURIComponent(tournamentId)}` : null,
  );

  const order = ['list', 'teams', 'bracket', 'branding'] as const;

  const steps = $derived(
    base
      ? [
          { id: 'list' as const, label: 'Турниры', href: '/admin' },
          { id: 'teams' as const, label: 'Команды', href: base },
          { id: 'bracket' as const, label: 'Сетка', href: `${base}/bracket` },
          { id: 'branding' as const, label: 'Оформление', href: `${base}/branding` },
        ]
      : [{ id: 'list' as const, label: 'Турниры', href: '/admin' }],
  );

  function stateOf(id: (typeof order)[number]): 'done' | 'current' | 'todo' {
    const ci = order.indexOf(current);
    const si = order.indexOf(id);
    if (si < ci) return 'done';
    if (si === ci) return 'current';
    return 'todo';
  }
</script>

<nav class="stepper mobile-only" aria-label="Шаги настройки турнира">
  <ol>
    {#each steps as step, i (step.id)}
      {@const st = stateOf(step.id)}
      <li class={st}>
        {#if i > 0}<span class="sep" aria-hidden="true"></span>{/if}
        {#if st === 'current'}
          <span class="pill" aria-current="step">
            <span class="num">{i + 1}</span>
            {step.label}
          </span>
        {:else}
          <a class="pill" href={step.href} data-state={st}>
            <span class="num">{i + 1}</span>
            {step.label}
          </a>
        {/if}
      </li>
    {/each}
  </ol>
</nav>

<style>
  .stepper {
    margin: 0 0 1.1rem;
  }
  @media (min-width: 900px) {
    .mobile-only {
      display: none;
    }
  }
  ol {
    list-style: none;
    margin: 0;
    padding: 0.55rem;
    display: flex;
    flex-wrap: nowrap;
    gap: 0.25rem;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
  }
  li {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
  }
  .sep {
    width: 1.1rem;
    height: 2px;
    margin: 0 0.15rem;
    background: var(--border);
    border-radius: 1px;
  }
  li.done .sep {
    background: color-mix(in srgb, var(--accent) 55%, var(--border));
  }
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    min-height: 2.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    text-decoration: none;
    color: var(--muted);
    font-weight: 600;
    font-size: 0.88rem;
    white-space: nowrap;
  }
  .pill:hover {
    color: var(--accent);
  }
  .num {
    display: inline-grid;
    place-items: center;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 999px;
    background: #ebe6dc;
    color: var(--muted);
    font-size: 0.75rem;
  }
  li.current .pill {
    background: color-mix(in srgb, var(--accent) 12%, white);
    color: var(--accent);
  }
  li.current .num {
    background: var(--accent);
    color: #fff;
  }
  li.done .num {
    background: color-mix(in srgb, var(--accent) 25%, white);
    color: var(--accent);
  }
  li.done .pill {
    color: var(--ink);
  }
</style>
