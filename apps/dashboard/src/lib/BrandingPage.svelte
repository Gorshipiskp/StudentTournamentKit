<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getBranding,
    getOrganizerToken,
    getTournament,
    setOrganizerToken,
    uploadBranding,
    type BrandingPublic,
    type TournamentPublic,
  } from './api';
  import WizardNav from './WizardNav.svelte';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let branding = $state<BrandingPublic | null>(null);
  let primary = $state('#3d9a86');
  let accent = $state('#c9a227');
  let logoFile = $state<File | null>(null);
  let error = $state<string | null>(null);
  let msg = $state<string | null>(null);
  let busy = $state(false);

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
      branding = await getBranding(tournamentId);
      if (branding.colors.primary) primary = String(branding.colors.primary);
      if (branding.colors.accent) accent = String(branding.colors.accent);
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

  async function onSave(e: Event) {
    e.preventDefault();
    busy = true;
    msg = null;
    try {
      branding = await uploadBranding(tournamentId, {
        colors: { primary, accent },
        logo: logoFile,
      });
      logoFile = null;
      msg = 'Брендинг сохранён — overlay обновит лого/цвета';
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
      <h1>Брендинг</h1>
      {#if tournament}
        <p class="sub">{tournament.name}</p>
      {/if}
    </div>
  </header>

  <WizardNav {tournamentId} current="branding" />

  {#if error}
    <p class="err">{error}</p>
  {/if}
  {#if msg}
    <p class="ok">{msg}</p>
  {/if}

  <section class="panel callout">
    <p>
      Логотип и цвета видны в эфирном overlay. Шаг необязательный — можно пропустить и вернуться
      к <a href={`/admin/tournaments/${encodeURIComponent(tournamentId)}/bracket`}>сетке</a>.
    </p>
  </section>

  <section class="panel">
    <h2>Логотип и цвета</h2>
    <p class="hint">Лого ≤ 2 МБ (PNG/JPEG/WebP). Цвета попадут в эфирный overlay.</p>
    <form class="form" onsubmit={onSave}>
      <label>
        Основной цвет
        <input type="color" bind:value={primary} />
        <input type="text" bind:value={primary} maxlength="7" />
      </label>
      <label>
        Акцент
        <input type="color" bind:value={accent} />
        <input type="text" bind:value={accent} maxlength="7" />
      </label>
      <label>
        Логотип
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          onchange={(e) => {
            const input = e.currentTarget as HTMLInputElement;
            logoFile = input.files?.[0] || null;
          }}
        />
      </label>
      {#if branding?.has_logo}
        <p class="hint">
          Текущее лого:
          <img
            class="preview"
            src={`/api/v1/tournaments/${encodeURIComponent(tournamentId)}/branding/logo`}
            alt="logo"
          />
        </p>
      {/if}
      <button type="submit" disabled={busy}>Сохранить</button>
    </form>
  </section>
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
    padding: 1.1rem 1.2rem;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    color: var(--muted);
    font-size: 0.9rem;
  }
  input[type='text'],
  input[type='file'] {
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
    font-weight: 600;
    cursor: pointer;
    align-self: flex-start;
  }
  button:disabled {
    opacity: 0.55;
  }
  a.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.5rem 0.9rem;
    text-decoration: none;
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
  .preview {
    display: block;
    margin-top: 0.4rem;
    max-height: 64px;
    max-width: 160px;
    object-fit: contain;
    background: #0003;
    border-radius: 4px;
  }
  .callout p {
    margin: 0;
    line-height: 1.45;
  }
  .callout a {
    color: var(--accent);
    font-weight: 600;
  }
</style>
