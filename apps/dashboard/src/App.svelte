<script lang="ts">
  import { onMount } from 'svelte';
  import {
    isAdminBracketPath,
    isAdminBrandingPath,
    isAdminPath,
    resolveAdminTournamentId,
    resolveMatchId,
  } from './lib/api';
  import AdminPage from './lib/AdminPage.svelte';
  import BracketPage from './lib/BracketPage.svelte';
  import BrandingPage from './lib/BrandingPage.svelte';
  import DirectorPage from './lib/DirectorPage.svelte';
  import TeamsPage from './lib/TeamsPage.svelte';

  let mode = $state<
    'boot' | 'admin' | 'teams' | 'bracket' | 'branding' | 'director' | 'error'
  >('boot');
  let matchId = $state<string | null>(null);
  let tournamentId = $state<string | null>(null);
  let error = $state<string | null>(null);

  onMount(() => {
    const path = window.location.pathname;
    if (isAdminPath(path)) {
      const tid = resolveAdminTournamentId(path);
      if (tid && isAdminBrandingPath(path)) {
        tournamentId = tid;
        mode = 'branding';
      } else if (tid && isAdminBracketPath(path)) {
        tournamentId = tid;
        mode = 'bracket';
      } else if (tid) {
        tournamentId = tid;
        mode = 'teams';
      } else {
        mode = 'admin';
      }
      return;
    }
    const id = resolveMatchId(path, window.location.search);
    matchId = id;
    if (!id) {
      mode = 'error';
      error = 'Откройте /director/{matchId} или /admin';
    } else {
      mode = 'director';
    }
  });
</script>

{#if mode === 'admin'}
  <AdminPage />
{:else if mode === 'teams' && tournamentId}
  <TeamsPage {tournamentId} />
{:else if mode === 'bracket' && tournamentId}
  <BracketPage {tournamentId} />
{:else if mode === 'branding' && tournamentId}
  <BrandingPage {tournamentId} />
{:else if mode === 'error'}
  <main class="boot">
    <h1>Панель режиссёра</h1>
    <p>{error}</p>
    <p class="hint">
      Пример: <code>/director/m_dev</code> · админ: <code>/admin</code>
    </p>
  </main>
{:else if mode === 'director' && matchId}
  <DirectorPage {matchId} />
{:else}
  <main class="boot"><p>Загрузка…</p></main>
{/if}

<style>
  .boot {
    max-width: 40rem;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }
  .hint {
    color: var(--muted);
  }
  code {
    background: var(--panel);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
  }
</style>
