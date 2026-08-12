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
  import MatchOps from './MatchOps.svelte';
  import WizardNav from './WizardNav.svelte';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let teams = $state<TeamPublic[]>([]);
  let nodes = $state<BracketNodePublic[]>([]);
  let error = $state<string | null>(null);
  let msg = $state<string | null>(null);
  let busy = $state(false);
  let size = $state(4);

  onMount(() => {
    if (!getOrganizerToken()) {
      window.location.href = '/admin';
      return;
    }
    void reload();
  });

  async function reload() {
    error = null;
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
      error = text;
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

  async function onGenerate() {
    busy = true;
    msg = null;
    try {
      await generateBracket(tournamentId, {
        size: Number(size),
        replace: nodes.length > 0,
      });
      msg = `Сетка на ${size} создана`;
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onAssign(node: BracketNodePublic, slot: 'a' | 'b', teamId: string) {
    busy = true;
    msg = null;
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
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  let maxRound = $derived(nodes.reduce((m, n) => Math.max(m, n.round), 0));
  let incompleteSlots = $derived(
    nodes.filter((n) => n.round === 0 && (!n.team_a_id || !n.team_b_id)).length,
  );
  let matchesReady = $derived(nodes.filter((n) => n.match_id).length);
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

<main class="admin">
  <header class="head">
    <div>
      <p class="brand">StudentTournamentKit</p>
      <h1>Сетка и старт</h1>
      {#if tournament}
        <p class="sub">{tournament.name}</p>
      {/if}
    </div>
  </header>

  <WizardNav {tournamentId} current="bracket" />

  {#if error}
    <p class="err">{error}</p>
  {/if}
  {#if msg}
    <p class="ok">{msg}</p>
  {/if}

  {#if teams.length < 4}
    <section class="panel callout">
      <p>
        Для сетки нужно минимум 4 команды. Сейчас: {teams.length}.
        <a href={`/admin/tournaments/${encodeURIComponent(tournamentId)}`}>Добавить команды →</a>
      </p>
    </section>
  {:else if nodes.length === 0}
    <section class="panel callout">
      <p>Сетки ещё нет — нажмите «Создать сетку» ниже, затем расставьте команды по слотам.</p>
    </section>
  {:else if incompleteSlots > 0}
    <section class="panel callout">
      <p>
        Не заполнены слоты первого раунда: {incompleteSlots}. Пока пара неполная — матч не
        создаётся. Когда слоты полные — появится «Старт (Fake)» и ссылки.
      </p>
    </section>
  {:else if matchesReady > 0}
    <section class="panel callout ok-box">
      <p>
        Готовых матчей: {matchesReady}. Запустите нужный и скопируйте ссылки режиссёру, судье и
        комментаторам.
      </p>
    </section>
  {/if}

  <section class="panel">
    <h2>Создать сетку на выбывание</h2>
    <p class="hint">
      Выберите команды в слоты вручную. Когда обе стороны заняты — система создаёт матч.
    </p>
    <div class="form row">
      <label>
        Число команд
        <select bind:value={size} disabled={busy}>
          <option value={4}>4</option>
          <option value={8}>8</option>
        </select>
      </label>
      <button type="button" disabled={busy} onclick={onGenerate}>
        {nodes.length ? 'Пересоздать сетку' : 'Создать сетку'}
      </button>
    </div>
  </section>

  {#each byRound as [round, list] (round)}
    <section class="panel">
      <h2>{roundLabel(round, maxRound)}</h2>
      <ul class="nodes">
        {#each list as node (node.id)}
          <li>
            <div class="slot">
              <span class="pos">#{node.position + 1}</span>
              <label>
                Команда A
                <select
                  disabled={busy}
                  value={node.team_a_id || ''}
                  onchange={(e) =>
                    onAssign(node, 'a', (e.currentTarget as HTMLSelectElement).value)}
                >
                  <option value="">—</option>
                  {#each teams as t (t.id)}
                    <option value={t.id}>{t.name}</option>
                  {/each}
                </select>
              </label>
              <span class="vs">vs</span>
              <label>
                Команда B
                <select
                  disabled={busy}
                  value={node.team_b_id || ''}
                  onchange={(e) =>
                    onAssign(node, 'b', (e.currentTarget as HTMLSelectElement).value)}
                >
                  <option value="">—</option>
                  {#each teams as t (t.id)}
                    <option value={t.id}>{t.name}</option>
                  {/each}
                </select>
              </label>
            </div>
            <div class="meta">
              {#if node.match_id}
                Матч: <code>{node.match_id}</code>
                · <a href={`/director/${encodeURIComponent(node.match_id)}`}>режиссёр</a>
                <MatchOps matchId={node.match_id} />
              {:else if node.team_a_id && node.team_b_id}
                Пара готова…
              {:else}
                {teamName(node.team_a_id)} vs {teamName(node.team_b_id)} — слоты неполные
              {/if}
              {#if node.source_a_node_id}
                <span class="src">источники: победители предыдущего раунда</span>
              {/if}
            </div>
          </li>
        {/each}
      </ul>
    </section>
  {:else}
    <p class="hint">Сетки пока нет — создайте выше.</p>
  {/each}
</main>

<style>
  .admin {
    max-width: 48rem;
    margin: 0 auto;
    padding: 2rem 1.25rem 3rem;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }
  .brand {
    margin: 0;
    color: var(--accent);
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  h1 {
    margin: 0.2rem 0 0;
    font-size: 1.6rem;
    font-weight: 650;
  }
  .sub {
    margin: 0.25rem 0 0;
    color: var(--muted);
  }
  h2 {
    margin: 0 0 0.75rem;
    font-size: 1.1rem;
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.1rem 1.2rem 1.25rem;
    margin-bottom: 1rem;
  }
  .form.row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: flex-end;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.9rem;
    color: var(--muted);
  }
  select {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--ink);
    border-radius: 4px;
    padding: 0.45rem 0.55rem;
  }
  button,
  a.link {
    background: var(--accent);
    color: #0b1210;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
    cursor: pointer;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
  }
  button:disabled {
    opacity: 0.55;
  }
  a.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    font-weight: 500;
  }
  .hint {
    color: var(--muted);
    font-size: 0.92rem;
  }
  .err {
    color: var(--danger);
  }
  .ok {
    color: var(--ok);
  }
  .nodes {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .nodes li {
    padding: 0.75rem 0;
    border-top: 1px solid var(--border);
  }
  .slot {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    align-items: flex-end;
  }
  .pos {
    color: var(--muted);
    font-size: 0.85rem;
    min-width: 1.5rem;
  }
  .vs {
    color: var(--muted);
    padding-bottom: 0.45rem;
  }
  .meta {
    margin-top: 0.45rem;
    font-size: 0.85rem;
    color: var(--muted);
  }
  .meta a {
    color: var(--accent);
  }
  .src {
    display: block;
    margin-top: 0.2rem;
  }
  code {
    font-size: 0.8rem;
  }
  .callout p {
    margin: 0;
    line-height: 1.45;
  }
  .callout a {
    color: var(--accent);
    font-weight: 600;
  }
  .ok-box {
    border-color: var(--ok);
  }
</style>
