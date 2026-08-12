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
  import WizardNav from './WizardNav.svelte';

  let token = $state<string | null>(null);
  let username = $state('organizer');
  let password = $state('');
  let loginError = $state<string | null>(null);
  let busy = $state(false);

  let items = $state<TournamentPublic[]>([]);
  let listError = $state<string | null>(null);
  let newName = $state('');
  let delayHint = $state(30);
  let actionMsg = $state<string | null>(null);
  let lastCreatedId = $state<string | null>(null);

  function humanError(raw: string): string {
    if (raw.startsWith('401')) return 'Неверный логин или пароль, либо сессия истекла.';
    if (raw.startsWith('404')) return 'Не найдено. Обновите список турниров.';
    if (raw.startsWith('400')) {
      try {
        const j = JSON.parse(raw.slice(raw.indexOf('{')));
        if (j.detail) return String(j.detail);
      } catch {
        /* ignore */
      }
    }
    return raw;
  }

  onMount(() => {
    token = getOrganizerToken();
    if (token) void refreshList();
  });

  async function refreshList() {
    listError = null;
    try {
      const res = await listTournaments();
      items = res.items;
    } catch (e) {
      listError = humanError(e instanceof Error ? e.message : String(e));
      if ((e instanceof Error ? e.message : String(e)).startsWith('401')) {
        setOrganizerToken(null);
        token = null;
      }
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
      await refreshList();
    } catch (err) {
      loginError = humanError(err instanceof Error ? err.message : String(err));
    } finally {
      busy = false;
    }
  }

  function onLogout() {
    setOrganizerToken(null);
    token = null;
    items = [];
    actionMsg = null;
  }

  async function onCreate(e: Event) {
    e.preventDefault();
    actionMsg = null;
    busy = true;
    try {
      const created = await createTournament({
        name: newName.trim() || 'Новый турнир',
        format: 'single_elim',
        settings: { configured_broadcast_delay_seconds: Number(delayHint) || 0 },
      });
      newName = '';
      lastCreatedId = created.id;
      actionMsg = `Черновик «${created.name}» создан. Дальше — добавьте команды.`;
      await refreshList();
    } catch (err) {
      actionMsg = humanError(err instanceof Error ? err.message : String(err));
    } finally {
      busy = false;
    }
  }

  async function onPublish(id: string) {
    actionMsg = null;
    busy = true;
    try {
      const t = await publishTournament(id);
      actionMsg = `Турнир «${t.name}» опубликован. Можно вести параллельно с другими.`;
      await refreshList();
    } catch (err) {
      actionMsg = humanError(err instanceof Error ? err.message : String(err));
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
</script>

<main class="admin">
  <header class="head">
    <div>
      <p class="brand">StudentTournamentKit</p>
      <h1>Админ турниров</h1>
    </div>
    {#if token}
      <button type="button" class="ghost" onclick={onLogout} disabled={busy}>Выйти</button>
    {/if}
  </header>

  {#if !token}
    <section class="panel">
      <h2>Вход организатора</h2>
      <p class="hint">Логин инстанса из настроек сервера (не облачный аккаунт).</p>
      <form class="form" onsubmit={onLogin}>
        <label>
          Имя пользователя
          <input bind:value={username} autocomplete="username" required />
        </label>
        <label>
          Пароль
          <input
            type="password"
            bind:value={password}
            autocomplete="current-password"
            required
          />
        </label>
        {#if loginError}
          <p class="err">{loginError}</p>
        {/if}
        <button type="submit" disabled={busy}>Войти</button>
      </form>
    </section>
  {:else}
    <WizardNav current="list" />

    <section class="panel how">
      <h2>Как провести турнир</h2>
      <ol>
        <li>Создайте черновик (название).</li>
        <li>Добавьте команды и игроков.</li>
        <li>Соберите сетку, расставьте команды, запустите матч (Fake) и скопируйте ссылки.</li>
        <li>По желанию загрузите лого и цвета (брендинг).</li>
      </ol>
      <p class="hint">Несколько турниров на одном инстансе не мешают друг другу.</p>
    </section>

    <section class="panel">
      <h2>Создать турнир</h2>
      <form class="form row" onsubmit={onCreate}>
        <label class="grow">
          Название
          <input bind:value={newName} placeholder="Кубок вуза" required />
        </label>
        <label>
          Задержка эфира (сек)
          <input type="number" min="0" bind:value={delayHint} />
        </label>
        <button type="submit" disabled={busy}>Создать черновик</button>
      </form>
      {#if lastCreatedId}
        <p class="next">
          <a class="cta" href={`/admin/tournaments/${encodeURIComponent(lastCreatedId)}`}
            >Перейти к командам →</a
          >
        </p>
      {/if}
    </section>

    <section class="panel">
      <div class="list-head">
        <h2>Ваши турниры</h2>
        <button type="button" class="ghost" onclick={() => refreshList()} disabled={busy}
          >Обновить</button
        >
      </div>
      {#if listError}
        <p class="err">{listError}</p>
      {/if}
      {#if actionMsg}
        <p class="ok">{actionMsg}</p>
      {/if}
      {#if items.length === 0}
        <p class="hint">Пока нет турниров — создайте черновик выше. Можно вести несколько сразу.</p>
      {:else}
        <ul class="list">
          {#each items as t (t.id)}
            <li>
              <div>
                <strong>{t.name || '(без названия)'}</strong>
                <span class="meta">{statusLabel(t.status)} · на выбывание</span>
              </div>
              <div class="actions">
                <a class="cta link" href={`/admin/tournaments/${encodeURIComponent(t.id)}`}
                  >Открыть</a
                >
                {#if t.status === 'draft'}
                  <button type="button" disabled={busy} onclick={() => onPublish(t.id)}
                    >Опубликовать</button
                  >
                {/if}
              </div>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  {/if}
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
    margin-bottom: 1.5rem;
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
  button {
    background: var(--accent);
    color: #0b1210;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
    cursor: pointer;
    font-weight: 600;
  }
  button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  button.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    font-weight: 500;
  }
  a.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    font-weight: 500;
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
  }
  .hint {
    color: var(--muted);
    margin: 0 0 1rem;
    font-size: 0.92rem;
  }
  .err {
    color: var(--danger);
    margin: 0;
  }
  .ok {
    color: var(--ok);
    margin: 0 0 0.75rem;
  }
  .list-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .list li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 0;
    border-top: 1px solid var(--border);
  }
  .actions {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    align-items: center;
  }
  a.link {
    text-decoration: none;
    display: inline-block;
  }
  .meta {
    display: block;
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: 0.15rem;
  }
  .how ol {
    margin: 0 0 0.75rem;
    padding-left: 1.2rem;
    color: var(--ink);
    line-height: 1.45;
  }
  .how .hint {
    margin: 0;
  }
  .next {
    margin: 0.85rem 0 0;
  }
  a.cta {
    display: inline-block;
    background: var(--accent);
    color: #0b1210;
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
    font-weight: 600;
    text-decoration: none;
  }
</style>
