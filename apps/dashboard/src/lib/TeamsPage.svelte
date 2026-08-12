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
  import AdminShell from './AdminShell.svelte';
  import AdminStepper from './AdminStepper.svelte';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import { humanApiError, toastErr, toastOk } from './toast';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let teams = $state<TeamPublic[]>([]);
  let busy = $state(false);
  let loading = $state(true);

  let newTeamName = $state('');
  let newTeamTag = $state('');
  let playerDraft = $state<Record<string, string>>({});
  let editingId = $state<string | null>(null);
  let editName = $state('');
  let teamNameInput = $state<HTMLInputElement | null>(null);

  let confirmOpen = $state(false);
  let confirmTitle = $state('');
  let confirmBody = $state('');
  let confirmAction = $state<(() => Promise<void>) | null>(null);

  const need = 4;
  let progress = $derived(Math.min(100, Math.round((teams.length / need) * 100)));
  let readyForBracket = $derived(teams.length >= need);

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
      const res = await listTeams(tournamentId);
      teams = res.items;
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

  async function onAddTeam(e: Event) {
    e.preventDefault();
    busy = true;
    try {
      await createTeam(tournamentId, {
        name: newTeamName.trim(),
        tag: newTeamTag.trim(),
      });
      newTeamName = '';
      newTeamTag = '';
      toastOk('Команда добавлена');
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  function startRename(team: TeamPublic) {
    editingId = team.id;
    editName = team.name;
  }

  async function saveRename(team: TeamPublic) {
    const name = editName.trim();
    if (!name || name === team.name) {
      editingId = null;
      return;
    }
    busy = true;
    try {
      await patchTeam(tournamentId, team.id, { name });
      editingId = null;
      toastOk('Название обновлено');
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  function askDeleteTeam(team: TeamPublic) {
    confirmTitle = 'Удалить команду?';
    confirmBody = `«${team.name}» и все игроки будут удалены.`;
    confirmAction = async () => {
      busy = true;
      try {
        await deleteTeam(tournamentId, team.id);
        toastOk(`Удалена: ${team.name}`);
        await reload();
      } catch (err) {
        toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
      } finally {
        busy = false;
        confirmOpen = false;
      }
    };
    confirmOpen = true;
  }

  async function onAddPlayer(team: TeamPublic) {
    const nick = (playerDraft[team.id] || '').trim();
    if (!nick) return;
    busy = true;
    try {
      await createPlayer(tournamentId, team.id, { nickname: nick });
      playerDraft = { ...playerDraft, [team.id]: '' };
      toastOk('Игрок добавлен');
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  function askDeletePlayer(team: TeamPublic, playerId: string, nick: string) {
    confirmTitle = 'Удалить игрока?';
    confirmBody = `Убрать «${nick}» из команды «${team.name}»?`;
    confirmAction = async () => {
      busy = true;
      try {
        await deletePlayer(tournamentId, team.id, playerId);
        toastOk('Игрок удалён');
        await reload();
      } catch (err) {
        toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
      } finally {
        busy = false;
        confirmOpen = false;
      }
    };
    confirmOpen = true;
  }
</script>

<AdminShell
  title="Команды"
  subtitle={`${teams.length} / ${need} для сетки`}
  tournamentName={tournament?.name ?? null}
  {tournamentId}
  current="teams"
  {loading}
>
  {#snippet footer()}
    {#if readyForBracket}
      <a class="btn btn-primary" href={`/admin/tournaments/${encodeURIComponent(tournamentId)}/bracket`}
        >К сетке →</a
      >
    {:else}
      <span class="muted">Ещё {need - teams.length}</span>
    {/if}
  {/snippet}

  <AdminStepper {tournamentId} current="teams" tournamentName={tournament?.name ?? null} />

  <div class="prog" class:ready={readyForBracket} role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
    <span style={`width: ${progress}%`}></span>
  </div>

  <section class="surface">
    <h2 class="display">Добавить команду</h2>
    <form class="form row" onsubmit={onAddTeam}>
      <label class="field grow">
        Название
        <input bind:this={teamNameInput} bind:value={newTeamName} placeholder="Alpha" required />
      </label>
      <label class="field">
        Тег
        <input bind:value={newTeamTag} placeholder="ALP" maxlength="16" />
      </label>
      <button type="submit" class="btn btn-primary" disabled={busy}>
        {busy ? 'Добавляем…' : 'Добавить'}
      </button>
    </form>
  </section>

  {#each teams as team (team.id)}
    <section class="surface team">
      <div class="team-head">
        {#if editingId === team.id}
          <form
            class="rename"
            onsubmit={(e) => {
              e.preventDefault();
              void saveRename(team);
            }}
          >
            <label class="field grow">
              Новое название
              <input bind:value={editName} required />
            </label>
            <button type="submit" class="btn btn-primary" disabled={busy}>Сохранить</button>
            <button type="button" class="btn btn-ghost" onclick={() => (editingId = null)}
              >Отмена</button
            >
          </form>
        {:else}
          <div>
            <h2>
              {team.name}{#if team.tag}
                <span class="tag muted">[{team.tag}]</span>{/if}
            </h2>
            <span class="muted">{team.players.length} игрок(ов)</span>
          </div>
          <div class="actions">
            <button type="button" class="btn btn-ghost" disabled={busy} onclick={() => startRename(team)}
              >Переименовать</button
            >
            <button
              type="button"
              class="btn btn-danger"
              disabled={busy}
              onclick={() => askDeleteTeam(team)}>Удалить</button
            >
          </div>
        {/if}
      </div>

      <ul class="players">
        {#each team.players as p (p.id)}
          <li>
            <span>{p.nickname}{#if p.is_coach} <em class="muted">(тренер)</em>{/if}</span>
            <button
              type="button"
              class="btn btn-ghost"
              disabled={busy}
              onclick={() => askDeletePlayer(team, p.id, p.nickname)}>Убрать</button
            >
          </li>
        {:else}
          <li class="empty muted">Пока нет игроков — добавьте ники ниже</li>
        {/each}
      </ul>

      <form
        class="form row"
        onsubmit={(e) => {
          e.preventDefault();
          void onAddPlayer(team);
        }}
      >
        <label class="field grow">
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
        <button type="submit" class="btn btn-primary" disabled={busy}>Добавить игрока</button>
      </form>
    </section>
  {:else}
    <p class="empty muted">Добавьте первую команду формой выше.</p>
  {/each}

  <ConfirmDialog
    open={confirmOpen}
    title={confirmTitle}
    body={confirmBody}
    oncancel={() => {
      confirmOpen = false;
      confirmAction = null;
    }}
    onconfirm={() => {
      void confirmAction?.();
    }}
  />
</AdminShell>

<style>
  .prog {
    height: 6px;
    border-radius: 999px;
    background: var(--bg-input);
    overflow: hidden;
    margin-bottom: 1rem;
    border: 1px solid var(--border);
  }
  .prog.ready {
    border-color: color-mix(in srgb, var(--ok) 40%, var(--border));
  }
  .prog span {
    display: block;
    height: 100%;
    background: var(--accent);
    border-radius: inherit;
    transition: width 0.25s ease;
  }
  .empty {
    margin: 0.75rem 0 0;
  }
  h2 {
    margin: 0 0 0.75rem;
    font-size: 1.15rem;
  }
  .team h2 {
    margin: 0;
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
  .team {
    margin-top: 0.85rem;
  }
  .team-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .actions,
  .rename {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    align-items: flex-end;
  }
  .rename {
    width: 100%;
  }
  .tag {
    font-weight: 500;
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
    gap: 0.5rem;
    padding: 0.45rem 0;
    border-top: 1px solid var(--border);
    min-height: var(--touch);
  }
  .players .empty {
    border-top: none;
  }
  em {
    font-style: normal;
    font-size: 0.85rem;
  }
</style>
