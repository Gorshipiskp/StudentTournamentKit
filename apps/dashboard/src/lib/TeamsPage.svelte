<script lang="ts">
  import { onMount } from 'svelte';
  import {
    createPlayer,
    createTeam,
    deletePlayer,
    deleteTeam,
    getOrganizerToken,
    getTournament,
    listTeams,
    patchTeam,
    setOrganizerToken,
    type TeamPublic,
    type TournamentPublic,
  } from './api';
  import WizardNav from './WizardNav.svelte';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let teams = $state<TeamPublic[]>([]);
  let error = $state<string | null>(null);
  let msg = $state<string | null>(null);
  let busy = $state(false);

  let newTeamName = $state('');
  let newTeamTag = $state('');
  let playerDraft = $state<Record<string, string>>({});

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
      const res = await listTeams(tournamentId);
      teams = res.items;
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

  async function onAddTeam(e: Event) {
    e.preventDefault();
    busy = true;
    msg = null;
    try {
      await createTeam(tournamentId, {
        name: newTeamName.trim(),
        tag: newTeamTag.trim(),
      });
      newTeamName = '';
      newTeamTag = '';
      msg = 'Команда добавлена';
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onRename(team: TeamPublic) {
    const name = window.prompt('Новое название команды', team.name);
    if (name === null) return;
    busy = true;
    msg = null;
    try {
      await patchTeam(tournamentId, team.id, { name });
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onDeleteTeam(team: TeamPublic) {
    if (!window.confirm(`Удалить команду «${team.name}» и всех игроков?`)) return;
    busy = true;
    msg = null;
    try {
      await deleteTeam(tournamentId, team.id);
      msg = `Удалена: ${team.name}`;
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onAddPlayer(team: TeamPublic) {
    const nick = (playerDraft[team.id] || '').trim();
    if (!nick) return;
    busy = true;
    msg = null;
    try {
      await createPlayer(tournamentId, team.id, { nickname: nick });
      playerDraft = { ...playerDraft, [team.id]: '' };
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onDeletePlayer(team: TeamPublic, playerId: string, nick: string) {
    if (!window.confirm(`Удалить игрока «${nick}»?`)) return;
    busy = true;
    try {
      await deletePlayer(tournamentId, team.id, playerId);
      await reload();
    } catch (err) {
      msg = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }
</script>

<main class="admin">
  <header class="head">
    <div>
      <p class="brand">StudentTournamentKit</p>
      <h1>Команды</h1>
      {#if tournament}
        <p class="sub">{tournament.name}</p>
      {/if}
    </div>
  </header>

  <WizardNav {tournamentId} current="teams" />

  {#if error}
    <p class="err">{error}</p>
  {/if}
  {#if msg}
    <p class="ok">{msg}</p>
  {/if}

  {#if teams.length === 0}
    <section class="panel callout">
      <p>
        Пока нет команд. Добавьте <strong>4</strong> (или 8) команд с игроками — потом соберёте
        сетку на выбывание.
      </p>
    </section>
  {:else if teams.length < 4}
    <section class="panel callout">
      <p>
        Сейчас команд: <strong>{teams.length}</strong>. Для сетки на 4 нужно ещё
        {4 - teams.length}. Имена не должны повторяться в этом турнире.
      </p>
    </section>
  {:else}
    <section class="panel callout ok-box">
      <p>
        Команд: {teams.length}. Можно перейти к сетке.
        <a href={`/admin/tournaments/${encodeURIComponent(tournamentId)}/bracket`}
          >Собрать сетку →</a
        >
      </p>
    </section>
  {/if}

  <section class="panel">
    <h2>Добавить команду</h2>
    <form class="form row" onsubmit={onAddTeam}>
      <label class="grow">
        Название
        <input bind:value={newTeamName} placeholder="Alpha" required />
      </label>
      <label>
        Тег
        <input bind:value={newTeamTag} placeholder="ALP" maxlength="16" />
      </label>
      <button type="submit" disabled={busy}>Добавить</button>
    </form>
  </section>

  {#each teams as team (team.id)}
    <section class="panel">
      <div class="list-head">
        <div>
          <h2>{team.name}{#if team.tag} <span class="tag">[{team.tag}]</span>{/if}</h2>
          <span class="meta">{team.players.length} игрок(ов)</span>
        </div>
        <div class="actions">
          <button type="button" class="ghost" disabled={busy} onclick={() => onRename(team)}
            >Переименовать</button
          >
          <button type="button" class="ghost danger" disabled={busy} onclick={() => onDeleteTeam(team)}
            >Удалить</button
          >
        </div>
      </div>

      <ul class="players">
        {#each team.players as p (p.id)}
          <li>
            <span>{p.nickname}{#if p.is_coach} <em>(тренер)</em>{/if}</span>
            <button
              type="button"
              class="ghost"
              disabled={busy}
              onclick={() => onDeletePlayer(team, p.id, p.nickname)}>Удалить</button
            >
          </li>
        {:else}
          <li class="empty">Пока нет игроков</li>
        {/each}
      </ul>

      <form
        class="form row"
        onsubmit={(e) => {
          e.preventDefault();
          void onAddPlayer(team);
        }}
      >
        <label class="grow">
          Ник игрока
          <input
            value={playerDraft[team.id] || ''}
            oninput={(e) => {
              playerDraft = {
                ...playerDraft,
                [team.id]: (e.currentTarget as HTMLInputElement).value,
              };
            }}
            placeholder="nickname"
          />
        </label>
        <button type="submit" disabled={busy}>Добавить игрока</button>
      </form>
    </section>
  {/each}
</main>

<style>
  .admin {
    max-width: 42rem;
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
    margin: 0;
    font-size: 1.1rem;
  }
  .tag {
    color: var(--muted);
    font-weight: 500;
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.1rem 1.2rem 1.25rem;
    margin-bottom: 1rem;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .form.row {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: flex-end;
  }
  .grow {
    flex: 1 1 12rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.9rem;
    color: var(--muted);
  }
  input {
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
    cursor: not-allowed;
  }
  button.ghost,
  a.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    font-weight: 500;
  }
  button.danger {
    color: var(--danger);
  }
  .hint {
    color: var(--muted);
  }
  .err {
    color: var(--danger);
  }
  .ok {
    color: var(--ok);
  }
  .list-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .actions {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
  }
  .meta {
    color: var(--muted);
    font-size: 0.85rem;
  }
  .players {
    list-style: none;
    margin: 0 0 0.85rem;
    padding: 0;
  }
  .players li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0;
    border-top: 1px solid var(--border);
  }
  .players .empty {
    color: var(--muted);
    border-top: none;
  }
  em {
    color: var(--muted);
    font-style: normal;
    font-size: 0.85rem;
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
