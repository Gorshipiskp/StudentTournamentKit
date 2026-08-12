<script lang="ts">
  import { onMount } from 'svelte';
  import {
    SCENES,
    getMatch,
    getOverlay,
    getProduction,
    patchScene,
    postOverride,
    type MatchPublic,
    type OverlaySnapshot,
    type ProductionPublic,
    type SceneId,
  } from './api';

  let { matchId }: { matchId: string } = $props();

  let match = $state<MatchPublic | null>(null);
  let production = $state<ProductionPublic | null>(null);
  let overlay = $state<OverlaySnapshot | null>(null);
  let busy = $state(false);
  let flash = $state<string | null>(null);
  let err = $state<string | null>(null);

  let teamAName = $state('');
  let teamBName = $state('');
  let scoreA = $state('');
  let scoreB = $state('');

  async function refresh() {
    try {
      const [m, p, o] = await Promise.all([
        getMatch(matchId),
        getProduction(matchId),
        getOverlay(matchId),
      ]);
      match = m;
      production = p;
      overlay = o;
      err = null;
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    }
  }

  async function setScene(scene: SceneId) {
    busy = true;
    flash = null;
    try {
      production = await patchScene(matchId, scene);
      overlay = await getOverlay(matchId);
      flash = `Сцена эфира: ${scene}`;
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  async function submitOverride() {
    busy = true;
    flash = null;
    const body: Record<string, string | number> = {};
    if (teamAName.trim()) body.team_a_name = teamAName.trim();
    if (teamBName.trim()) body.team_b_name = teamBName.trim();
    if (scoreA !== '') body.score_team_a = Number(scoreA);
    if (scoreB !== '') body.score_team_b = Number(scoreB);
    try {
      overlay = await postOverride(matchId, body);
      flash = `Override применён (version ${overlay.version})`;
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  async function clearOverride() {
    busy = true;
    try {
      overlay = await postOverride(matchId, { clear: true });
      teamAName = '';
      teamBName = '';
      scoreA = '';
      scoreB = '';
      flash = 'Override сброшен';
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  onMount(() => {
    void refresh();
    const t = setInterval(() => void refresh(), 2000);
    return () => clearInterval(t);
  });

  const desired = $derived(production?.desired.scene ?? '—');
  const actual = $derived(production?.actual.scene ?? '—');
</script>

<main class="page">
  <header>
    <div>
      <p class="eyebrow">Режиссёр · только Platform API</p>
      <h1>Матч <code>{matchId}</code></h1>
    </div>
    <button type="button" class="ghost" onclick={() => refresh()} disabled={busy}>
      Обновить
    </button>
  </header>

  {#if err}
    <p class="banner bad" role="alert">{err}</p>
  {/if}
  {#if flash}
    <p class="banner ok">{flash}</p>
  {/if}

  <section class="grid">
    <article class="card">
      <h2>Матч</h2>
      {#if match}
        <dl>
          <div><dt>Статус</dt><dd>{match.status}</dd></div>
          <div><dt>Счёт</dt><dd>{match.score.team_a} : {match.score.team_b}</dd></div>
          <div><dt>Раунд</dt><dd>{match.round}</dd></div>
          <div><dt>Карта</dt><dd>{match.map ?? '—'}</dd></div>
          <div><dt>Фаза</dt><dd>{match.phase ?? '—'}</dd></div>
          {#if match.judge_banner}
            <div><dt>Судья</dt><dd class="warn">{match.judge_banner}</dd></div>
          {/if}
        </dl>
      {:else}
        <p class="muted">Нет данных</p>
      {/if}
    </article>

    <article class="card">
      <h2>Агент / OBS</h2>
      {#if production}
        <dl>
          <div><dt>Desired</dt><dd>{desired}</dd></div>
          <div><dt>Actual</dt><dd>{actual}</dd></div>
          <div>
            <dt>Агент</dt>
            <dd class:ok={production.agent_status === 'connected'}>{production.agent_status}</dd>
          </div>
          <div>
            <dt>OBS</dt>
            <dd class:ok={production.obs_status === 'connected'}>{production.obs_status}</dd>
          </div>
          <div><dt>Эфир</dt><dd>{production.broadcast_status}</dd></div>
        </dl>
        <p class="note">OBS меняет только Director Agent — не эта панель.</p>
      {:else}
        <p class="muted">Нет данных</p>
      {/if}
    </article>

    <article class="card">
      <h2>Overlay</h2>
      {#if overlay}
        <dl>
          <div><dt>Version</dt><dd>{overlay.version}</dd></div>
          <div><dt>Сцена</dt><dd>{overlay.data.scene}</dd></div>
          <div>
            <dt>Команды</dt>
            <dd>
              {overlay.data.team_a.name} {overlay.data.team_a.score} :
              {overlay.data.team_b.score} {overlay.data.team_b.name}
            </dd>
          </div>
        </dl>
      {:else}
        <p class="muted">Нет данных</p>
      {/if}
    </article>
  </section>

  <section class="card scenes">
    <h2>Сцена эфира</h2>
    <p class="muted">Меняет desired на Platform → Agent применяет в OBS.</p>
    <div class="scene-row">
      {#each SCENES as scene}
        <button
          type="button"
          class:active={desired === scene}
          disabled={busy}
          onclick={() => setScene(scene)}
        >
          {scene}
        </button>
      {/each}
    </div>
  </section>

  <section class="card">
    <h2>Override overlay</h2>
    <p class="muted">Временные имена/счёт на эфире (через Platform, не OBS).</p>
    <form
      class="override"
      onsubmit={(e) => {
        e.preventDefault();
        void submitOverride();
      }}
    >
      <label>
        Команда A
        <input bind:value={teamAName} placeholder="Alpha" />
      </label>
      <label>
        Команда B
        <input bind:value={teamBName} placeholder="Beta" />
      </label>
      <label>
        Счёт A
        <input bind:value={scoreA} type="number" min="0" />
      </label>
      <label>
        Счёт B
        <input bind:value={scoreB} type="number" min="0" />
      </label>
      <div class="actions">
        <button type="submit" disabled={busy}>Применить</button>
        <button type="button" class="ghost" disabled={busy} onclick={() => clearOverride()}>
          Сбросить
        </button>
      </div>
    </form>
  </section>
</main>

<style>
  .page {
    max-width: 960px;
    margin: 0 auto;
    padding: 1.5rem 1.25rem 3rem;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.25rem;
  }

  .eyebrow {
    margin: 0 0 0.25rem;
    color: var(--accent);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.75rem;
  }

  h1 {
    margin: 0;
    font-size: 1.45rem;
  }

  h2 {
    margin: 0 0 0.75rem;
    font-size: 1.05rem;
  }

  code {
    font-size: 0.95em;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
  }

  dl {
    margin: 0;
    display: grid;
    gap: 0.45rem;
  }

  dl > div {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
  }

  dt {
    color: var(--muted);
  }

  dd {
    margin: 0;
    font-weight: 600;
  }

  dd.ok {
    color: var(--ok);
  }

  dd.warn {
    color: var(--warn);
  }

  .muted,
  .note {
    color: var(--muted);
    font-size: 0.9rem;
  }

  .note {
    margin: 0.75rem 0 0;
  }

  .scene-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  button {
    background: var(--accent);
    color: #04110e;
    border: none;
    border-radius: 4px;
    padding: 0.55rem 0.9rem;
    font-weight: 600;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
    background: var(--accent-hover);
  }

  button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  button.active {
    outline: 2px solid #fff;
    outline-offset: 1px;
  }

  button.ghost {
    background: transparent;
    color: var(--ink);
    border: 1px solid var(--border);
  }

  .override {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.75rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.85rem;
    color: var(--muted);
  }

  input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--ink);
    padding: 0.45rem 0.55rem;
  }

  .actions {
    grid-column: 1 / -1;
    display: flex;
    gap: 0.5rem;
  }

  .banner {
    padding: 0.55rem 0.8rem;
    border-radius: 4px;
    margin: 0 0 1rem;
  }

  .banner.ok {
    background: rgba(91, 184, 106, 0.15);
    color: var(--ok);
  }

  .banner.bad {
    background: rgba(196, 92, 92, 0.18);
    color: var(--danger);
  }
</style>
