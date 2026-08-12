<script lang="ts">
  import { onMount } from 'svelte';
  import {
    createTournament,
    getOrganizerToken,
    listTournaments,
    loginOrganizer,
    publishTournament,
    setOrganizerToken,
    type TournamentPublic,
  } from './api';
  import AdminShell from './AdminShell.svelte';
  import AdminStepper from './AdminStepper.svelte';
  import ToastHost from './ToastHost.svelte';
  import { humanApiError, toastErr, toastOk } from './toast';

  let token = $state<string | null>(null);
  let username = $state('organizer');
  let password = $state('');
  let loginError = $state<string | null>(null);
  let busy = $state(false);
  let loading = $state(false);

  let items = $state<TournamentPublic[]>([]);
  let newName = $state('');
  let delayHint = $state(90);
  let lastCreatedId = $state<string | null>(null);
  let showCreate = $state(false);
  let query = $state('');
  let nameInput = $state<HTMLInputElement | null>(null);

  let filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (t) =>
        (t.name || '').toLowerCase().includes(q) ||
        t.id.toLowerCase().includes(q) ||
        statusLabel(t.status).toLowerCase().includes(q),
    );
  });

  onMount(() => {
    token = getOrganizerToken();
    if (token) void refreshList(true);
  });

  async function refreshList(initial = false) {
    if (initial) loading = true;
    try {
      const res = await listTournaments();
      items = res.items;
      if (items.length === 0) showCreate = true;
    } catch (e) {
      const raw = e instanceof Error ? e.message : String(e);
      toastErr(humanApiError(raw));
      if (raw.startsWith('401')) {
        setOrganizerToken(null);
        token = null;
      }
    } finally {
      loading = false;
    }
  }

  async function onLogin(e: Event) {
    e.preventDefault();
    loginError = null;
    busy = true;
    try {
      const res = await loginOrganizer(username, password);
      setOrganizerToken(res.access_token);
      token = res.access_token;
      password = '';
      await refreshList(true);
      toastOk('Вы вошли');
    } catch (err) {
      loginError = humanApiError(err instanceof Error ? err.message : String(err));
    } finally {
      busy = false;
    }
  }

  function onLogout() {
    setOrganizerToken(null);
    token = null;
    items = [];
    lastCreatedId = null;
  }

  async function onCreate(e: Event) {
    e.preventDefault();
    busy = true;
    try {
      const created = await createTournament({
        name: newName.trim() || 'Новый турнир',
        format: 'single_elim',
        settings: { configured_broadcast_delay_seconds: Number(delayHint) || 0 },
      });
      newName = '';
      lastCreatedId = created.id;
      showCreate = false;
      toastOk(`Турнир «${created.name}» создан — добавьте команды`);
      await refreshList();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  async function onPublish(id: string) {
    busy = true;
    try {
      const t = await publishTournament(id);
      toastOk(`«${t.name}» опубликован`);
      await refreshList();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }

  function statusLabel(s: string): string {
    if (s === 'draft') return 'Черновик';
    if (s === 'published') return 'Опубликован';
    if (s === 'completed') return 'Завершён';
    return s;
  }

  function statusBadge(s: string): string {
    if (s === 'draft') return 'badge-draft';
    if (s === 'published') return 'badge-published';
    if (s === 'completed') return 'badge-completed';
    return 'badge-idle';
  }

  function openCreate() {
    showCreate = true;
    queueMicrotask(() => nameInput?.focus());
  }
</script>

{#if !token}
  <div class="admin-app">
    <main class="login">
      <div class="hero surface">
        <p class="mark">STK</p>
        <h1 class="display">Организатор</h1>
        <p class="lead muted">Войдите, чтобы создать турнир и раздать ссылки команде эфира.</p>
        <form class="form" onsubmit={onLogin}>
          <label class="field">
            Логин
            <input bind:value={username} autocomplete="username" required />
          </label>
          <label class="field">
            Пароль
            <input
              type="password"
              bind:value={password}
              autocomplete="current-password"
              required
            />
          </label>
          {#if loginError}
            <p class="err" role="alert">{loginError}</p>
          {/if}
          <button type="submit" class="btn btn-primary" disabled={busy}>
            {busy ? 'Входим…' : 'Войти'}
          </button>
        </form>
      </div>
      <ToastHost />
    </main>
  </div>
{:else}
  <AdminShell title="Турниры" current="list" showLogout {loading} onlogout={onLogout}>
    <AdminStepper current="list" />

    <div class="toolbar">
      {#if items.length > 1}
        <label class="field search">
          <span class="sr-only">Найти турнир</span>
          <input bind:value={query} placeholder="Найти…" type="search" />
        </label>
      {:else}
        <span class="muted count">{items.length ? `${items.length} турнир(а)` : ''}</span>
      {/if}
      <div class="toolbar-actions">
        <button type="button" class="btn btn-ghost" disabled={busy || loading} onclick={() => refreshList()}
          >Обновить</button
        >
        <button type="button" class="btn btn-primary" disabled={busy} onclick={openCreate}>
          Создать
        </button>
      </div>
    </div>

    {#if showCreate || items.length === 0}
      <section class="surface create">
        <h2 class="display">Новый турнир</h2>
        <form class="form row" onsubmit={onCreate}>
          <label class="field grow">
            Название
            <input bind:this={nameInput} bind:value={newName} placeholder="Кубок вуза" required />
          </label>
          <button type="submit" class="btn btn-primary" disabled={busy}>
            {busy ? 'Создаём…' : 'Создать'}
          </button>
          {#if showCreate && items.length > 0}
            <button type="button" class="btn btn-ghost" onclick={() => (showCreate = false)}
              >Отмена</button
            >
          {/if}
        </form>
        <details class="more">
          <summary class="muted">Дополнительно</summary>
          <label class="field">
            Задержка эфира (сек)
            <input type="number" min="0" bind:value={delayHint} />
          </label>
        </details>
      </section>
    {/if}

    {#if lastCreatedId}
      <p class="next-bar">
        <a class="btn btn-primary" href={`/admin/tournaments/${encodeURIComponent(lastCreatedId)}`}
          >К командам →</a
        >
      </p>
    {/if}

    {#if items.length === 0 && !loading}
      <p class="empty muted">Создайте первый турнир формой выше.</p>
    {:else if filtered.length === 0 && query}
      <p class="empty muted">
        Ничего не найдено.
        <button type="button" class="btn btn-ghost" onclick={() => (query = '')}>Сбросить</button>
      </p>
    {:else}
      <ul class="tour-list">
        {#each filtered as t (t.id)}
          <li class="surface tourney">
            <div class="info">
              <strong class="name">{t.name || 'Без названия'}</strong>
              <div class="meta">
                <span class="badge {statusBadge(t.status)}">{statusLabel(t.status)}</span>
              </div>
            </div>
            <div class="actions">
              {#if t.status === 'draft'}
                <button type="button" class="btn btn-ghost" disabled={busy} onclick={() => onPublish(t.id)}
                  >Опубликовать</button
                >
              {/if}
              <a class="btn btn-primary" href={`/admin/tournaments/${encodeURIComponent(t.id)}`}
                >Открыть</a
              >
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </AdminShell>
{/if}

<style>
  .login {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 1.5rem;
  }
  .hero {
    width: min(24rem, 100%);
    padding: 1.75rem 1.5rem 1.5rem;
  }
  .mark {
    display: inline-grid;
    place-items: center;
    width: 2.6rem;
    height: 2.6rem;
    margin: 0 0 0.75rem;
    border-radius: var(--radius);
    background: var(--cta);
    color: var(--cta-text);
    font-weight: 700;
  }
  h1 {
    margin: 0;
    font-size: 1.55rem;
  }
  .lead {
    margin: 0.55rem 0 1.15rem;
    line-height: 1.4;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }
  .form.row {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: flex-end;
  }
  .grow {
    flex: 1 1 14rem;
  }
  .err {
    margin: 0;
    color: var(--danger);
    font-size: 0.92rem;
  }
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.85rem;
  }
  .count {
    font-size: 0.9rem;
  }
  .toolbar-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-left: auto;
  }
  .search {
    flex: 1 1 12rem;
    max-width: 18rem;
    margin: 0;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
  .create {
    margin-bottom: 1rem;
  }
  .create h2 {
    margin: 0 0 0.75rem;
    font-size: 1.15rem;
  }
  .more {
    margin-top: 0.75rem;
  }
  .more summary {
    cursor: pointer;
    font-size: 0.88rem;
    margin-bottom: 0.5rem;
  }
  .next-bar {
    margin: 0 0 1rem;
  }
  .empty {
    margin: 0.5rem 0 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
  }
  .tour-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }
  .tourney {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }
  .name {
    font-size: 1.05rem;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    margin-top: 0.3rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
</style>
