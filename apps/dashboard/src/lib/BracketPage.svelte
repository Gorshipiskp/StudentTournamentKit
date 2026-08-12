<script lang="ts">
  import { onMount } from 'svelte';
  import {
    assignBracketNode,
    generateBracket,
    getBracket,
    getOrganizerToken,
    getTournament,
    listTeams,
    setOrganizerToken,
    type BracketNodePublic,
    type TeamPublic,
    type TournamentPublic,
  } from './api';
  import AdminShell from './AdminShell.svelte';
  import AdminStepper from './AdminStepper.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import MatchOps from './MatchOps.svelte';
  import { humanApiError, toastErr, toastOk } from './toast';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let teams = $state<TeamPublic[]>([]);
  let nodes = $state<BracketNodePublic[]>([]);
  let busy = $state(false);
  let loading = $state(true);
  let size = $state(4);
  let confirmOpen = $state(false);

  onMount(() => {
    if (!getOrganizerToken()) {
      window.location.href = '/admin';
      return;
    }
    void reload();
  });

  async function reload() {
    try {
      tournament = await getTournament(tournamentId);
      const [tRes, bRes] = await Promise.all([
        listTeams(tournamentId),
        getBracket(tournamentId),
      ]);
      teams = tRes.items;
      nodes = bRes.items;
    } catch (e) {
      const text = e instanceof Error ? e.message : String(e);
      if (text.startsWith('401')) {
        setOrganizerToken(null);
        window.location.href = '/admin';
        return;
      }
      toastErr(humanApiError(text));
    } finally {
      loading = false;
    }
  }

  function teamName(id: string | null): string {
    if (!id) return '—';
    return teams.find((t) => t.id === id)?.name || id.slice(0, 8);
  }

  function roundLabel(r: number, maxRound: number): string {
    if (r === maxRound) return 'Финал';
    if (r === maxRound - 1 && maxRound > 0) return 'Полуфинал';
    return `Раунд ${r + 1}`;
  }

  function requestGenerate() {
    if (nodes.length > 0) {
      confirmOpen = true;
      return;
    }
    void doGenerate();
  }

  async function doGenerate() {
    confirmOpen = false;
    busy = true;
    try {
      await generateBracket(tournamentId, {
        size: Number(size),
        replace: nodes.length > 0,
      });
      toastOk(`Сетка на ${size} команд создана`);
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  async function onAssign(node: BracketNodePublic, slot: 'a' | 'b', teamId: string) {
    busy = true;
    try {
      const body =
        slot === 'a'
          ? teamId
            ? { team_a_id: teamId }
            : { clear_team_a: true }
          : teamId
            ? { team_b_id: teamId }
            : { clear_team_b: true };
      await assignBracketNode(tournamentId, node.id, body);
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  let maxRound = $derived(nodes.reduce((m, n) => Math.max(m, n.round), 0));
  let incompleteSlots = $derived(
    nodes.filter((n) => n.round === 0 && (!n.team_a_id || !n.team_b_id)).length,
  );
  let matchesReady = $derived(nodes.filter((n) => n.match_id).length);
  let firstMatchId = $derived(nodes.find((n) => n.match_id)?.match_id ?? null);
  let byRound = $derived.by(() => {
    const map = new Map<number, BracketNodePublic[]>();
    for (const n of nodes) {
      const list = map.get(n.round) || [];
      list.push(n);
      map.set(n.round, list);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  });
</script>

<AdminShell
  title="Сетка"
  subtitle={nodes.length
    ? incompleteSlots
      ? `Заполните слоты (${incompleteSlots})`
      : matchesReady
        ? `${matchesReady} матч(ей) готовы`
        : null
    : teams.length < 4
      ? `Нужно ещё ${4 - teams.length} команд`
      : 'Создайте сетку'}
  tournamentName={tournament?.name ?? null}
  {tournamentId}
  current="bracket"
  {loading}
>
  {#snippet footer()}
    {#if matchesReady > 0 && firstMatchId}
      <a class="btn btn-ghost" href={`/director/${encodeURIComponent(firstMatchId)}`}
        >Режиссёр</a
      >
      <a class="btn btn-primary" href={`#match-${encodeURIComponent(firstMatchId)}`}
        >К запуску</a
      >
    {:else if teams.length < 4}
      <a class="btn btn-primary" href={`/admin/tournaments/${encodeURIComponent(tournamentId)}`}
        >К командам</a
      >
    {:else if incompleteSlots > 0}
      <span class="muted">Заполните пары первого раунда</span>
    {:else if nodes.length === 0}
      <span class="muted">Создайте сетку выше</span>
    {/if}
  {/snippet}

  <AdminStepper {tournamentId} current="bracket" tournamentName={tournament?.name ?? null} />

  <section class="surface">
    <h2 class="display">{nodes.length ? 'Пересоздать сетку' : 'Создать сетку'}</h2>
    <div class="form row">
      <label class="field">
        Команд в сетке
        <select bind:value={size} disabled={busy}>
          <option value={4}>4</option>
          <option value={8}>8</option>
        </select>
      </label>
      <button
        type="button"
        class="btn btn-primary"
        disabled={busy || teams.length < 4}
        onclick={requestGenerate}
      >
        {busy ? 'Создаём…' : nodes.length ? 'Пересоздать' : 'Создать'}
      </button>
    </div>
  </section>

  {#if byRound.length}
    <div class="rounds">
      {#each byRound as [round, list] (round)}
        <section class="surface round-col">
          <h2 class="display">{roundLabel(round, maxRound)}</h2>
          <ul class="nodes">
            {#each list as node (node.id)}
              <li class="node" class:ready={!!node.match_id}>
                <div class="slot">
                  <span class="pos muted">#{node.position + 1}</span>
                  <label class="field">
                    Команда A
                    <select
                      disabled={busy}
                      value={node.team_a_id || ''}
                      onchange={(e) =>
                        onAssign(node, 'a', (e.currentTarget as HTMLSelectElement).value)}
                    >
                      <option value="">— пусто —</option>
                      {#each teams as t (t.id)}
                        <option value={t.id}>{t.name}</option>
                      {/each}
                    </select>
                  </label>
                  <span class="vs muted">vs</span>
                  <label class="field">
                    Команда B
                    <select
                      disabled={busy}
                      value={node.team_b_id || ''}
                      onchange={(e) =>
                        onAssign(node, 'b', (e.currentTarget as HTMLSelectElement).value)}
                    >
                      <option value="">— пусто —</option>
                      {#each teams as t (t.id)}
                        <option value={t.id}>{t.name}</option>
                      {/each}
                    </select>
                  </label>
                </div>
                {#if node.match_id}
                  <div id={`match-${node.match_id}`}>
                    <MatchOps matchId={node.match_id} />
                  </div>
                {:else if node.team_a_id && node.team_b_id}
                  <p class="meta muted">Пара готова — матч создаётся…</p>
                {:else}
                  <p class="meta muted">
                    {teamName(node.team_a_id)} vs {teamName(node.team_b_id)} — заполните оба слота
                  </p>
                {/if}
                {#if node.source_a_node_id}
                  <p class="src muted">Сюда проходят победители предыдущего раунда</p>
                {/if}
              </li>
            {/each}
          </ul>
        </section>
      {/each}
    </div>
  {:else}
    <p class="muted empty-note">Сетки пока нет.</p>
  {/if}

  <ConfirmDialog
    open={confirmOpen}
    title="Пересоздать сетку?"
    body="Текущие слоты и привязки матчей будут сброшены. Это действие нельзя отменить."
    confirmLabel="Пересоздать"
    danger={true}
    oncancel={() => (confirmOpen = false)}
    onconfirm={() => void doGenerate()}
  />
</AdminShell>

<style>
  .surface {
    margin-bottom: 1rem;
  }
  h2 {
    margin: 0 0 0.65rem;
    font-size: 1.15rem;
  }
  .form.row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: flex-end;
  }
  .empty-note {
    margin: 0.25rem 0 0;
  }
  .rounds {
    display: grid;
    gap: 1rem;
  }
  @media (min-width: 1000px) {
    .rounds {
      grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
      align-items: start;
    }
  }
  .nodes {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .node {
    padding: 0.85rem 0;
    border-top: 1px solid var(--border);
  }
  .node:first-child {
    border-top: none;
    padding-top: 0;
  }
  .node.ready {
    background: color-mix(in srgb, var(--ok) 6%, transparent);
    margin: 0 -0.65rem;
    padding-left: 0.65rem;
    padding-right: 0.65rem;
    border-radius: var(--radius);
  }
  .slot {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    align-items: flex-end;
  }
  .pos {
    font-size: 0.85rem;
    min-width: 1.5rem;
    padding-bottom: 0.7rem;
  }
  .vs {
    padding-bottom: 0.7rem;
    font-weight: 650;
  }
  .field {
    flex: 1 1 9rem;
  }
  .meta,
  .src {
    margin: 0.45rem 0 0;
    font-size: 0.85rem;
  }
</style>
